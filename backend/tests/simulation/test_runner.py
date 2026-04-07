import pytest

from core.agents.sim_agent import SimAgent
from core.agents.prompts import build_doctor_prompt, build_patient_prompt
from core.db.queries.simulations import create_simulation, get_simulation, get_simulation_turns
from core.llm.mock import MockProvider
from core.simulation import Simulation, SimulationStatus
from core.types import AgentProfile, AgentStep, AgentTrace, Role, Scenario, TurnEndEvent, TurnStartEvent

DOCTOR = AgentProfile(name="Dr. Test", role=Role.DOCTOR, traits={}, backstory="")
PATIENT = AgentProfile(name="Patient Test", role=Role.PATIENT, traits={}, backstory="")
SCENARIO = Scenario(name="CBC", description="Medical Test: CBC\nResults: WBC: 11.2\nNormal Range: 4.5-11.0\nClinical Significance: Elevated")


@pytest.fixture
def provider():
    return MockProvider(delay=0)


def _make_sim(db, provider, max_turns=8):
    rec = create_simulation(db, persona_name=PATIENT.name, scenario_name=SCENARIO.name, model="mock:default", config={})
    d = SimAgent(provider, "default", DOCTOR, build_doctor_prompt(DOCTOR, SCENARIO))
    p = SimAgent(provider, "default", PATIENT, build_patient_prompt(PATIENT))
    return Simulation(db, rec.id, d, p, max_turns=max_turns)


# ── State machine tests ──────────────────────────────────────────────────────


def test_initial_state_is_idle(db, provider):
    assert _make_sim(db, provider).state == SimulationStatus.IDLE


@pytest.mark.asyncio
async def test_run_completes(db, provider):
    sim = _make_sim(db, provider, max_turns=2)
    trace = await sim.run()
    assert sim.state == SimulationStatus.COMPLETED
    assert isinstance(trace, AgentTrace)


@pytest.mark.asyncio
async def test_short_produces_2_turns(db, provider):
    trace = await _make_sim(db, provider, max_turns=2).run()
    assert len(trace.steps) == 2


@pytest.mark.asyncio
async def test_long_produces_8_turns(db, provider):
    trace = await _make_sim(db, provider, max_turns=8).run()
    assert len(trace.steps) == 8


@pytest.mark.asyncio
async def test_alternating_agents(db, provider):
    trace = await _make_sim(db, provider, max_turns=8).run()
    for i, step in enumerate(trace.steps):
        expected = "doctor" if i % 2 == 0 else "patient"
        assert step.agent_type == expected


@pytest.mark.asyncio
async def test_step_executes_one_turn(db, provider):
    sim = _make_sim(db, provider, max_turns=2)
    step = await sim.step()
    assert isinstance(step, AgentStep)
    assert step.agent_type == "doctor"
    assert sim.turn == 1


@pytest.mark.asyncio
async def test_step_from_idle(db, provider):
    sim = _make_sim(db, provider, max_turns=2)
    await sim.step()
    assert sim.state == SimulationStatus.PAUSED


@pytest.mark.asyncio
async def test_step_until_completed(db, provider):
    sim = _make_sim(db, provider, max_turns=2)
    await sim.step()
    assert sim.state == SimulationStatus.PAUSED
    await sim.step()
    assert sim.state == SimulationStatus.COMPLETED


@pytest.mark.asyncio
async def test_step_past_max_raises(db, provider):
    sim = _make_sim(db, provider, max_turns=2)
    await sim.step()
    await sim.step()
    with pytest.raises(RuntimeError, match="All turns completed"):
        await sim.step()


@pytest.mark.asyncio
async def test_stop_from_paused(db, provider):
    sim = _make_sim(db, provider, max_turns=2)
    await sim.step()
    sim.stop()
    assert sim.state == SimulationStatus.COMPLETED


@pytest.mark.asyncio
async def test_pause_and_resume(db, provider):
    sim = _make_sim(db, provider, max_turns=8)
    await sim.step()
    assert len(sim.trace.steps) == 1
    await sim.step()
    assert len(sim.trace.steps) == 2
    sim.resume()
    trace = await sim.run()
    assert sim.state == SimulationStatus.COMPLETED
    assert len(trace.steps) == 8


# ── Invalid transitions ──────────────────────────────────────────────────────


def test_pause_from_idle_raises(db, provider):
    sim = _make_sim(db, provider)
    with pytest.raises(RuntimeError, match="must be running"):
        sim.pause()


def test_resume_from_idle_raises(db, provider):
    sim = _make_sim(db, provider)
    with pytest.raises(RuntimeError, match="must be paused"):
        sim.resume()


def test_stop_from_idle_raises(db, provider):
    sim = _make_sim(db, provider)
    with pytest.raises(RuntimeError, match="must be running or paused"):
        sim.stop()


# ── Trace integrity tests ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_trace_has_timing(db, provider):
    trace = await _make_sim(db, provider, max_turns=2).run()
    assert trace.duration_ms > 0
    for step in trace.steps:
        assert step.duration_ms >= 0


@pytest.mark.asyncio
async def test_no_step_errors(db, provider):
    trace = await _make_sim(db, provider, max_turns=8).run()
    for step in trace.steps:
        assert step.error is None


@pytest.mark.asyncio
async def test_step_outputs_are_nonempty(db, provider):
    trace = await _make_sim(db, provider, max_turns=2).run()
    for step in trace.steps:
        assert len(step.output.strip()) > 0


@pytest.mark.asyncio
async def test_step_has_correct_agent_type(db, provider):
    trace = await _make_sim(db, provider, max_turns=2).run()
    assert trace.steps[0].agent_type == "doctor"
    assert trace.steps[1].agent_type == "patient"


# ── Streaming tests ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_streaming_yields_events(db, provider):
    sim = _make_sim(db, provider, max_turns=2)
    events = [et async for et, _ in sim.run_streaming()]
    assert events.count("turn_start") == 2
    assert events.count("turn_end") == 2
    assert events.count("done") == 1
    assert events.count("token") > 0


@pytest.mark.asyncio
async def test_run_streaming_produces_trace(db, provider):
    sim = _make_sim(db, provider, max_turns=2)
    async for _ in sim.run_streaming():
        pass
    assert sim.state == SimulationStatus.COMPLETED
    assert len(sim.trace.steps) == 2


@pytest.mark.asyncio
async def test_streaming_tokens_match_output(db, provider):
    sim = _make_sim(db, provider, max_turns=2)
    turn_tokens, current = [], []
    async for et, data in sim.run_streaming():
        if et == "turn_start": current = []
        elif et == "token": current.append(data)
        elif et == "turn_end": turn_tokens.append(current)
    for i, tokens in enumerate(turn_tokens):
        assert "".join(tokens) == sim.trace.steps[i].output


@pytest.mark.asyncio
async def test_streaming_alternates_roles(db, provider):
    sim = _make_sim(db, provider, max_turns=2)
    roles = [data.role async for et, data in sim.run_streaming() if et == "turn_start"]
    assert roles == ["doctor", "patient"]


@pytest.mark.asyncio
async def test_streaming_typed_events(db, provider):
    sim = _make_sim(db, provider, max_turns=2)
    starts, ends = [], []
    async for et, data in sim.run_streaming():
        if et == "turn_start":
            assert isinstance(data, TurnStartEvent)
            starts.append(data)
        elif et == "turn_end":
            assert isinstance(data, TurnEndEvent)
            ends.append(data)
    assert len(starts) == 2
    assert starts[0].role == "doctor"
    assert starts[1].role == "patient"


# ── Persistence tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_persists_turns_to_db(db, provider):
    sim = _make_sim(db, provider, max_turns=2)
    await sim.run()
    turns = get_simulation_turns(db, sim.sim_id)
    assert len(turns) == 2
    assert turns[0].role == "doctor"
    assert turns[1].role == "patient"


@pytest.mark.asyncio
async def test_run_marks_simulation_completed(db, provider):
    sim = _make_sim(db, provider, max_turns=2)
    await sim.run()
    rec = get_simulation(db, sim.sim_id)
    assert rec.state == "completed"
    assert rec.duration_ms > 0


# ── Error handling tests ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_error_does_not_record_partial_output(db, provider):
    """When an agent errors mid-stream, no partial output should be in the transcript."""
    class FailingProvider(MockProvider):
        async def stream(self, messages, model):
            yield "partial"
            raise RuntimeError("boom")

    failing = FailingProvider(delay=0)
    rec = create_simulation(db, persona_name=PATIENT.name, scenario_name=SCENARIO.name, model="mock:default", config={})
    d = SimAgent(failing, "default", DOCTOR, build_doctor_prompt(DOCTOR, SCENARIO))
    p = SimAgent(failing, "default", PATIENT, build_patient_prompt(PATIENT))
    sim = Simulation(db, rec.id, d, p, max_turns=2)

    events = [et async for et, _ in sim.run_streaming()]
    assert "turn_error" in events
    assert sim.state == SimulationStatus.ERROR
    assert len(sim.transcript) == 0
    assert len(sim.trace.steps) == 0
