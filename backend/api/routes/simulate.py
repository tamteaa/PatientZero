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


@router.post("/simulate")
async def simulate(request: SimulateRequest):
    provider, model = parse_provider_model(request.model)

    persona = Persona(**request.persona.model_dump())
    scenario = Scenario(**request.scenario.model_dump())

    explainer = ExplainerAgent(provider, model, request.style, request.mode, scenario)
    patient = PatientAgent(provider, model, persona)

    sim = Simulation(explainer, patient, request.mode)

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
