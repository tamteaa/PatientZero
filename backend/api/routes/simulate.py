import json
from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from backend.api.dependencies import db, simulation_service
from core.agents.judge import JudgeAgent
from core.config.personas import PATIENT_PROFILES, DOCTOR_PROFILES
from core.config.scenarios import SCENARIOS
from core.db.queries.evaluations import (
    create_evaluation,
    delete_evaluation,
    get_evaluation,
    list_evaluations,
)
from core.db.queries.simulations import (
    delete_simulation,
    get_simulation,
    get_simulation_turns,
    list_simulations,
)
from core.llm.factory import parse_provider_model
from core.types import AgentProfile, Message, Scenario, Transcript

router = APIRouter()


@router.get("/personas")
def get_personas():
    return [asdict(p) for p in PATIENT_PROFILES]


@router.get("/doctors")
def get_doctors():
    return [asdict(p) for p in DOCTOR_PROFILES]


@router.get("/scenarios")
def get_scenarios():
    return [asdict(s) for s in SCENARIOS]


# ── Simulate ─────────────────────────────────────────────────────────────────


class SimulateRequest(BaseModel):
    patient_name: str
    doctor_name: str
    scenario_name: str
    model: str
    max_turns: int | None = None


def _find_profile(profiles: list[AgentProfile], name: str) -> AgentProfile | None:
    return next((p for p in profiles if p.name == name), None)


def _sse_event(event_type: str, data) -> dict | None:
    if event_type == "turn_start":
        return {"event": "turn_start", "data": json.dumps({"role": data.role, "turn": data.turn})}
    elif event_type == "token":
        return {"data": json.dumps({"token": data})}
    elif event_type == "turn_end":
        return {"event": "turn_end", "data": json.dumps({"role": data.role, "turn": data.turn})}
    elif event_type == "turn_error":
        return {"event": "turn_error", "data": json.dumps(data)}
    elif event_type == "done":
        return {"event": "done", "data": json.dumps({"simulation_id": data})}
    elif event_type == "sim_created":
        return {"event": "sim_created", "data": json.dumps({"simulation_id": data})}
    return None


@router.post("/simulate")
async def simulate(request: SimulateRequest):
    patient = _find_profile(PATIENT_PROFILES, request.patient_name)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    doctor = _find_profile(DOCTOR_PROFILES, request.doctor_name)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    scenario = next((s for s in SCENARIOS if s.test_name == request.scenario_name), None)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    sim_id = simulation_service.create_and_start(
        doctor, patient, scenario, request.model, request.max_turns or 8,
    )
    return {"simulation_id": sim_id}


@router.get("/simulations/{sim_id}/stream")
async def stream_simulation(sim_id: str):
    sim = simulation_service.get_active(sim_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not active")

    async def generate():
        async for event_type, data in sim.subscribe():
            event = _sse_event(event_type, data)
            if event:
                yield event

    return EventSourceResponse(generate())


# ── Simulation control ──────────────────────────────────────────────────────


def _get_active_sim(sim_id: str):
    sim = simulation_service.get_active(sim_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not active")
    return sim


@router.post("/simulations/{sim_id}/pause")
def pause_simulation(sim_id: str):
    sim = _get_active_sim(sim_id)
    try:
        sim.pause()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.post("/simulations/{sim_id}/resume")
def resume_simulation(sim_id: str):
    sim = _get_active_sim(sim_id)
    try:
        sim.resume()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.post("/simulations/{sim_id}/stop")
def stop_simulation(sim_id: str):
    sim = _get_active_sim(sim_id)
    try:
        sim.stop()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


# ── Simulation history ───────────────────────────────────────────────────────


@router.get("/simulations")
def get_all_simulations():
    return [s.to_dict() for s in list_simulations(db)]


@router.get("/simulations/{sim_id}")
def get_simulation_detail(sim_id: str):
    simulation = get_simulation(db, sim_id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    turns = get_simulation_turns(db, sim_id)
    result = {**simulation.to_dict(), "turns": [t.to_dict() for t in turns]}
    # Overlay live state from active simulation if it exists
    active = simulation_service.get_active(sim_id)
    if active:
        result["state"] = active.state.value
        result["text_status"] = active.text_status
    return result


@router.delete("/simulations/{sim_id}")
def delete_simulation_endpoint(sim_id: str):
    simulation = get_simulation(db, sim_id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    delete_simulation(db, sim_id)
    return {"ok": True}


# ── Judge evaluation ─────────────────────────────────────────────────────────


class EvaluateRequest(BaseModel):
    model: str = "mock:default"


@router.post("/simulations/{sim_id}/evaluate")
async def evaluate_simulation(sim_id: str, request: EvaluateRequest):
    simulation = get_simulation(db, sim_id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    if simulation.state != "completed":
        raise HTTPException(status_code=400, detail="Simulation must be completed before evaluation")

    turns = get_simulation_turns(db, sim_id)
    transcript = Transcript(messages=[Message(role=t.role, content=t.content) for t in turns])

    provider, model = parse_provider_model(request.model)
    judge = JudgeAgent(provider, model)
    result = await judge.evaluate(transcript)

    delete_evaluation(db, sim_id)
    evaluation = create_evaluation(db, sim_id, request.model, result)
    return evaluation.to_dict()


@router.get("/simulations/{sim_id}/evaluation")
def get_simulation_evaluation(sim_id: str):
    simulation = get_simulation(db, sim_id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    evaluation = get_evaluation(db, sim_id)
    return evaluation.to_dict() if evaluation else None


@router.get("/evaluations")
def get_all_evaluations():
    return [e.to_dict() for e in list_evaluations(db)]


