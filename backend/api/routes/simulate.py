"""Simulation endpoints — create, stream, control, inspect."""

import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from backend.api.dependencies import logger, repos
from core.config.settings import APP_SETTINGS, AVAILABLE_MODELS
from core.judge import Judge
from core.simulation import Simulation
from core.types import Message, Transcript

router = APIRouter()


@router.get("/models")
def get_models():
    return AVAILABLE_MODELS


# ── Create ─────────────────────────────────────────────────────────────────


class SimulateRequest(BaseModel):
    experiment_id: str
    model: str
    max_turns: int | None = Field(default=None, ge=1, le=50)
    # Per-agent trait constraints: {agent_name: {trait: value}}
    constraints: dict[str, dict[str, str]] = Field(default_factory=dict)


def _sse_event(event_type: str, data) -> dict | None:
    if event_type == "turn_start":
        return {"event": "turn_start", "data": json.dumps({"role": data.role, "turn": data.turn})}
    if event_type == "token":
        return {"data": json.dumps({"token": data})}
    if event_type == "turn_end":
        return {"event": "turn_end", "data": json.dumps({"role": data.role, "turn": data.turn})}
    if event_type == "turn_error":
        return {"event": "turn_error", "data": json.dumps(data)}
    if event_type == "done":
        return {"event": "done", "data": json.dumps({"simulation_id": data})}
    if event_type == "sim_created":
        return {"event": "sim_created", "data": json.dumps({"simulation_id": data})}
    return None


@router.post("/simulate")
async def simulate(request: SimulateRequest):
    if request.model not in AVAILABLE_MODELS:
        raise HTTPException(status_code=400, detail="Unknown model")

    experiment = repos.experiments.get(request.experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    sample_rng = repos.experiments.acquire_next_sample_rng(request.experiment_id)
    draw_index = experiment.sample_draw_index if sample_rng is not None else None

    try:
        profiles = {
            agent.name: agent.sample(
                rng=sample_rng,
                **request.constraints.get(agent.name, {}),
            )
            for agent in experiment.config.agents
        }
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid trait constraint: {e}")

    if Simulation.active_count() >= APP_SETTINGS.max_concurrent_simulations:
        raise HTTPException(
            status_code=429,
            detail=f"Max concurrent simulations reached ({APP_SETTINGS.max_concurrent_simulations})",
        )

    sim = Simulation.create(
        experiment,
        profiles,
        repos,
        logger=logger,
        model=request.model,
        max_turns=request.max_turns,
        draw_index=draw_index,
    )
    prior_on_done = sim.on_done

    def _finalize_log() -> None:
        final = repos.simulations.get(sim.sim_id)
        logger.close(
            sim.sim_id,
            state=final.state if final else "error",
            duration_ms=(final.duration_ms or 0.0) if final else 0.0,
        )
        if prior_on_done:
            prior_on_done()

    sim.on_done = _finalize_log
    sim.start()
    return {"simulation_id": sim.sim_id}


@router.get("/simulations/{sim_id}/stream")
async def stream_simulation(sim_id: str):
    sim = Simulation.get_active(sim_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not active")

    async def generate():
        async for event_type, data in sim.subscribe():
            event = _sse_event(event_type, data)
            if event:
                yield event

    return EventSourceResponse(generate())


# ── Control ────────────────────────────────────────────────────────────────


def _get_active_sim(sim_id: str):
    sim = Simulation.get_active(sim_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not active")
    return sim


@router.post("/simulations/{sim_id}/pause")
async def pause_simulation(sim_id: str):
    sim = _get_active_sim(sim_id)
    try:
        sim.pause()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.post("/simulations/{sim_id}/resume")
async def resume_simulation(sim_id: str):
    sim = _get_active_sim(sim_id)
    try:
        sim.resume()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.post("/simulations/{sim_id}/stop")
async def stop_simulation(sim_id: str):
    sim = _get_active_sim(sim_id)
    try:
        sim.stop()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


# ── Detail ─────────────────────────────────────────────────────────────────


@router.get("/simulations/{sim_id}")
def get_simulation_detail(sim_id: str):
    simulation = repos.simulations.get(sim_id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    turns = repos.simulations.get_turns(sim_id)
    result = {**simulation.to_dict(), "turns": [t.to_dict() for t in turns]}
    active = Simulation.get_active(sim_id)
    if active:
        result["state"] = active.state.value
        result["text_status"] = active.text_status
        result["max_turns"] = active.max_turns
    return result


@router.delete("/simulations/{sim_id}")
def delete_simulation_endpoint(sim_id: str):
    simulation = repos.simulations.get(sim_id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    repos.simulations.delete(sim_id)
    return {"ok": True}


# ── Judge evaluation ───────────────────────────────────────────────────────


@router.post("/simulations/{sim_id}/evaluate")
async def evaluate_simulation(sim_id: str):
    simulation = repos.simulations.get(sim_id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    if simulation.state != "completed":
        raise HTTPException(status_code=400, detail="Simulation must be completed before evaluation")

    experiment = repos.experiments.get(simulation.config.experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Parent experiment not found")

    turns = repos.simulations.get_turns(sim_id)
    transcript = Transcript(messages=[Message(role=t.role, content=t.content) for t in turns])

    jc = experiment.config.judge
    judge = Judge(
        rubric=dict(jc.rubric),
        instructions=jc.instructions,
        model=jc.model or simulation.config.model,
    )
    result = await judge.evaluate(transcript)

    repos.evaluations.delete_for_simulation(sim_id)
    evaluation = repos.evaluations.create_or_append(
        simulation_id=sim_id,
        experiment_id=experiment.id,
        judge_result=result,
    )
    return evaluation.to_dict()


@router.get("/simulations/{sim_id}/evaluation")
def get_simulation_evaluation(sim_id: str):
    simulation = repos.simulations.get(sim_id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    evaluation = repos.evaluations.get_latest_for_simulation(sim_id)
    return evaluation.to_dict() if evaluation else None
