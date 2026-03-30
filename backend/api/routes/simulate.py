import json
from dataclasses import asdict
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from backend.api.dependencies import db
from core.agents.explainer import ExplainerAgent
from core.agents.patient import PatientAgent
from core.config.personas import PERSONAS
from core.config.scenarios import SCENARIOS
from core.agents.judge import JudgeAgent
from core.db.queries.evaluations import (
    create_evaluation,
    delete_evaluation,
    get_evaluation,
    list_evaluations,
)
from core.db.queries.simulations import (
    add_simulation_turn,
    complete_simulation,
    create_simulation,
    delete_simulation,
    fail_simulation,
    get_simulation,
    get_simulation_turns,
    list_simulations,
)
from core.llm.factory import parse_provider_model
from core.simulation import Simulation
from core.types import Persona, Scenario, TurnEndEvent, TurnStartEvent

router = APIRouter()


# ── Data endpoints ───────────────────────────────────────────────────────────


@router.get("/personas")
def get_personas():
    return [asdict(p) for p in PERSONAS]


@router.get("/scenarios")
def get_scenarios():
    return [asdict(s) for s in SCENARIOS]


# ── Simulate ─────────────────────────────────────────────────────────────────


class PersonaRequest(BaseModel):
    name: str
    age: str
    education: str
    literacy_level: str
    anxiety: str
    prior_knowledge: str
    communication_style: str
    backstory: str


class ScenarioRequest(BaseModel):
    test_name: str
    results: str
    normal_range: str
    significance: str


class SimulateRequest(BaseModel):
    persona: PersonaRequest
    style: Literal["clinical", "analogy"]
    mode: Literal["static", "dialog"]
    scenario: ScenarioRequest
    model: str
    max_turns: int | None = None


@router.post("/simulate")
async def simulate(request: SimulateRequest):
    provider, model = parse_provider_model(request.model)

    persona = Persona(**request.persona.model_dump())
    scenario = Scenario(**request.scenario.model_dump())

    # Use the full scenario from config (includes quiz questions)
    full_scenario = next((s for s in SCENARIOS if s.test_name == scenario.test_name), scenario)

    explainer = ExplainerAgent(provider, model, request.style, request.mode, full_scenario)
    patient = PatientAgent(provider, model, persona)

    sim = Simulation(explainer, patient, request.mode, max_turns=request.max_turns)

    # Persist simulation
    sim_record = create_simulation(
        db,
        persona_name=persona.name,
        scenario_name=scenario.test_name,
        style=request.style,
        mode=request.mode,
        model=request.model,
        config=request.model_dump(),
    )
    sim_id = sim_record["id"]

    async def generate():
        try:
            async for event_type, data in sim.run_streaming():
                if event_type == "turn_start":
                    evt = data
                    yield {
                        "event": "turn_start",
                        "data": json.dumps({"role": evt.role, "turn": evt.turn, "simulation_id": sim_id}),
                    }
                elif event_type == "token":
                    yield {"data": json.dumps({"token": data})}
                elif event_type == "turn_end":
                    evt = data
                    # Find the step that just completed
                    step = sim.trace.steps[-1]
                    add_simulation_turn(
                        db,
                        sim_id=sim_id,
                        turn_number=evt.turn,
                        role=evt.role,
                        agent_type=step.agent_type,
                        content=step.output,
                        duration_ms=step.duration_ms,
                    )
                    yield {
                        "event": "turn_end",
                        "data": json.dumps({"role": evt.role, "turn": evt.turn}),
                    }
                elif event_type == "done":
                    complete_simulation(db, sim_id, sim.trace.duration_ms)
                    yield {
                        "event": "done",
                        "data": json.dumps({"simulation_id": sim_id}),
                    }
        except Exception:
            fail_simulation(db, sim_id)
            raise

    return EventSourceResponse(generate())


# ── Simulation history ───────────────────────────────────────────────────────


@router.get("/simulations")
def get_all_simulations():
    return list_simulations(db)


@router.get("/simulations/{sim_id}")
def get_simulation_detail(sim_id: str):
    simulation = get_simulation(db, sim_id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    turns = get_simulation_turns(db, sim_id)
    return {**simulation, "turns": turns}


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
    if simulation["state"] != "completed":
        raise HTTPException(status_code=400, detail="Simulation must be completed before evaluation")

    turns = get_simulation_turns(db, sim_id)
    main_turns = [t for t in turns if t["agent_type"] != "QuizResponse"]
    quiz_turns = [t for t in turns if t["agent_type"] == "QuizResponse"]

    transcript = [{"role": t["role"], "content": t["content"]} for t in main_turns]

    # Reconstruct quiz responses and answer key from stored turns + scenario config
    scenario_config = next(
        (s for s in SCENARIOS if s.test_name == simulation["scenario_name"]), None
    )
    answer_key = scenario_config.quiz if scenario_config else []
    quiz_responses = [
        {"question": answer_key[i]["question"], "answer": t["content"]}
        for i, t in enumerate(quiz_turns)
        if i < len(answer_key)
    ]

    provider, model = parse_provider_model(request.model)
    judge = JudgeAgent(provider, model)
    result = await judge.evaluate(
        transcript=transcript,
        quiz_responses=quiz_responses,
        answer_key=answer_key,
        mode=simulation["mode"],
    )

    # Overwrite any existing evaluation for this simulation
    delete_evaluation(db, sim_id)
    evaluation = create_evaluation(db, sim_id, request.model, result)
    return evaluation


@router.get("/simulations/{sim_id}/evaluation")
def get_simulation_evaluation(sim_id: str):
    simulation = get_simulation(db, sim_id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    evaluation = get_evaluation(db, sim_id)
    return evaluation  # None if not yet evaluated


@router.get("/evaluations")
def get_all_evaluations():
    return list_evaluations(db)


# ── Batch run ────────────────────────────────────────────────────────────────


class BatchRequest(BaseModel):
    model: str = "mock:default"
    skip_existing: bool = True


@router.post("/simulate/batch")
async def simulate_batch(request: BatchRequest):
    provider, model_str = parse_provider_model(request.model)

    existing: set[str] = set()
    if request.skip_existing:
        sims = list_simulations(db)
        existing = {
            f"{s['persona_name']}|{s['scenario_name']}|{s['style']}|{s['mode']}"
            for s in sims
        }

    combos = [
        (persona, scenario, style, mode)
        for persona in PERSONAS
        for scenario in SCENARIOS
        for style, mode in [
            ("clinical", "static"),
            ("clinical", "dialog"),
            ("analogy", "static"),
            ("analogy", "dialog"),
        ]
    ]
    total = len(combos)

    async def generate():
        yield {
            "event": "batch_start",
            "data": json.dumps({"total": total}),
        }

        succeeded = 0
        failed = 0
        skipped = 0

        for i, (persona, scenario, style, mode) in enumerate(combos):
            combo_key = f"{persona.name}|{scenario.test_name}|{style}|{mode}"

            if request.skip_existing and combo_key in existing:
                skipped += 1
                yield {
                    "event": "sim_skip",
                    "data": json.dumps({
                        "current": i + 1,
                        "total": total,
                        "persona": persona.name,
                        "scenario": scenario.test_name,
                        "style": style,
                        "mode": mode,
                    }),
                }
                continue

            yield {
                "event": "sim_start",
                "data": json.dumps({
                    "current": i + 1,
                    "total": total,
                    "persona": persona.name,
                    "scenario": scenario.test_name,
                    "style": style,
                    "mode": mode,
                }),
            }

            from dataclasses import asdict
            sim_record = create_simulation(
                db,
                persona_name=persona.name,
                scenario_name=scenario.test_name,
                style=style,
                mode=mode,
                model=request.model,
                config={
                    "persona": asdict(persona),
                    "scenario": asdict(scenario),
                    "style": style,
                    "mode": mode,
                    "model": request.model,
                },
            )
            sim_id = sim_record["id"]

            try:
                explainer = ExplainerAgent(provider, model_str, style, mode, scenario)
                patient = PatientAgent(provider, model_str, persona)
                sim = Simulation(explainer, patient, mode)

                async for event_type, data in sim.run_streaming():
                    if event_type == "turn_end":
                        step = sim.trace.steps[-1]
                        add_simulation_turn(
                            db,
                            sim_id=sim_id,
                            turn_number=data.turn,
                            role=data.role,
                            agent_type=step.agent_type,
                            content=step.output,
                            duration_ms=step.duration_ms,
                        )

                complete_simulation(db, sim_id, sim.trace.duration_ms)
                succeeded += 1
                yield {
                    "event": "sim_done",
                    "data": json.dumps({
                        "current": i + 1,
                        "total": total,
                        "sim_id": sim_id,
                        "persona": persona.name,
                        "scenario": scenario.test_name,
                        "style": style,
                        "mode": mode,
                        "state": "completed",
                        "duration_ms": sim.trace.duration_ms,
                    }),
                }
            except Exception as e:
                fail_simulation(db, sim_id)
                failed += 1
                yield {
                    "event": "sim_done",
                    "data": json.dumps({
                        "current": i + 1,
                        "total": total,
                        "sim_id": sim_id,
                        "persona": persona.name,
                        "scenario": scenario.test_name,
                        "style": style,
                        "mode": mode,
                        "state": "error",
                        "error": str(e),
                    }),
                }

        yield {
            "event": "batch_done",
            "data": json.dumps({
                "succeeded": succeeded,
                "failed": failed,
                "skipped": skipped,
                "total": total,
            }),
        }

    return EventSourceResponse(generate())
