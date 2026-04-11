import json
from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from backend.api.dependencies import db, simulation_service
from core.agents.judge import JudgeAgent
from core.config.personas import PATIENT_PROFILES, DOCTOR_PROFILES
from core.config.scenarios import SCENARIOS
from core.config.settings import APP_SETTINGS, AVAILABLE_MODELS, EXPLANATION_STYLES
from core.generators.profile import StaticPatientGenerator, StaticDoctorGenerator
from core.generators.static import StaticScenarioGenerator
from core.db.queries.evaluations import (
    create_evaluation,
    delete_evaluation,
    get_evaluation,
    list_evaluations,
)
from core.db.queries.experiments import get_experiment
from core.db.queries.simulations import (
    delete_simulation,
    get_simulation,
    get_simulation_turns,
    list_simulations,
)
from core.llm.factory import parse_provider_model
from core.types import AgentProfile, Message, Scenario, Transcript

router = APIRouter()


@router.get("/models")
def get_models():
    return AVAILABLE_MODELS


@router.get("/personas")
def get_personas():
    return [asdict(p) for p in PATIENT_PROFILES]


@router.get("/personas/generate")
def generate_personas(n: int = 10):
    """Generate n patient profiles sampled from real demographic distributions."""
    if n < 1 or n > 200:
        raise HTTPException(status_code=400, detail="n must be between 1 and 200")
    profiles = StaticPatientGenerator().generate(n)
    return [asdict(p) for p in profiles]


@router.get("/doctors")
def get_doctors():
    return [asdict(p) for p in DOCTOR_PROFILES]


@router.get("/doctors/generate")
def generate_doctors(n: int = 5):
    """Generate n doctor profiles sampled from RIAS/CAHPS distributions."""
    if n < 1 or n > 50:
        raise HTTPException(status_code=400, detail="n must be between 1 and 50")
    profiles = StaticDoctorGenerator().generate(n)
    return [asdict(p) for p in profiles]


@router.get("/scenarios")
def get_scenarios():
    return [asdict(s) for s in SCENARIOS]


@router.get("/styles")
def get_styles():
    return EXPLANATION_STYLES


@router.get("/scenarios/generate")
def generate_scenarios(n: int = 5, abnormal_ratio: float = 0.3):
    """Generate n scenarios sampled from medical test distributions."""
    if n < 1 or n > 50:
        raise HTTPException(status_code=400, detail="n must be between 1 and 50")
    if not 0.0 <= abnormal_ratio <= 1.0:
        raise HTTPException(status_code=400, detail="abnormal_ratio must be between 0 and 1")
    scenarios = StaticScenarioGenerator(abnormal_ratio=abnormal_ratio).generate(n)
    return [asdict(s) for s in scenarios]


# ── Simulate ─────────────────────────────────────────────────────────────────


class SimulateRequest(BaseModel):
    experiment_id: str
    model: str
    max_turns: int | None = Field(default=None, ge=1, le=50)
    style: str = "clinical"
    policy_version: str = "baseline"
    batch_id: str | None = Field(
        default=None,
        description="Optional label for feedback-loop batches (analysis/compare); stored in config_json only.",
    )
    # None or "random" → generate from StaticScenarioGenerator
    scenario_name: str | None = None
    # Optional trait constraints — None means sample from real distributions
    patient_literacy: str | None = None   # low | moderate | high
    patient_anxiety: str | None = None    # low | moderate | high
    doctor_empathy: str | None = None     # low | moderate | high
    doctor_verbosity: str | None = None   # terse | moderate | thorough


_VALID_LITERACY  = {"low", "moderate", "high"}
_VALID_ANXIETY   = {"low", "moderate", "high"}
_VALID_EMPATHY   = {"low", "moderate", "high"}
_VALID_VERBOSITY = {"terse", "moderate", "thorough"}


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
    if request.model not in AVAILABLE_MODELS:
        raise HTTPException(status_code=400, detail="Unknown model")

    if request.style not in EXPLANATION_STYLES:
        raise HTTPException(status_code=400, detail=f"style must be one of {EXPLANATION_STYLES}")

    experiment = get_experiment(db, request.experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Validate trait constraints
    if request.patient_literacy and request.patient_literacy not in _VALID_LITERACY:
        raise HTTPException(status_code=400, detail=f"patient_literacy must be one of {_VALID_LITERACY}")
    if request.patient_anxiety and request.patient_anxiety not in _VALID_ANXIETY:
        raise HTTPException(status_code=400, detail=f"patient_anxiety must be one of {_VALID_ANXIETY}")
    if request.doctor_empathy and request.doctor_empathy not in _VALID_EMPATHY:
        raise HTTPException(status_code=400, detail=f"doctor_empathy must be one of {_VALID_EMPATHY}")
    if request.doctor_verbosity and request.doctor_verbosity not in _VALID_VERBOSITY:
        raise HTTPException(status_code=400, detail=f"doctor_verbosity must be one of {_VALID_VERBOSITY}")

    if not request.scenario_name or request.scenario_name == "random":
        scenario = StaticScenarioGenerator().generate(n=1)[0]
    else:
        scenario = next((s for s in SCENARIOS if s.name == request.scenario_name), None)
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")

    patient = StaticPatientGenerator(distribution=experiment.patient_distribution).generate(
        n=1,
        literacy=request.patient_literacy,
        anxiety=request.patient_anxiety,
    )[0]
    doctor = StaticDoctorGenerator(distribution=experiment.doctor_distribution).generate(
        n=1,
        empathy=request.doctor_empathy,
        verbosity=request.doctor_verbosity,
    )[0]

    if len(simulation_service._active) >= APP_SETTINGS.max_concurrent_simulations:
        raise HTTPException(
            status_code=429,
            detail=f"Max concurrent simulations reached ({APP_SETTINGS.max_concurrent_simulations})",
        )

    sim_id = simulation_service.create_and_start(
        request.experiment_id,
        doctor,
        patient,
        scenario,
        request.model,
        style=request.style,
        policy_version=request.policy_version,
        batch_id=request.batch_id,
        max_turns=request.max_turns or 8,
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
        result["max_turns"] = active.max_turns
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
    judge_result = await judge.evaluate(transcript)
    judge_result.model = request.model

    delete_evaluation(db, sim_id)
    evaluation = create_evaluation(db, sim_id, judge_result)
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


