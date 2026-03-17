import asyncio

import pytest

from core.agents.explainer import ExplainerAgent
from core.agents.patient import PatientAgent
from core.llm.mock import MockProvider
from core.simulation import Simulation, SimulationStatus
from core.types import AgentStep, AgentTrace, Persona, Scenario, TurnEndEvent, TurnStartEvent

PERSONA = Persona(
    name="Maria Garcia",
    age="62",
    education="High school",
    literacy_level="low",
    anxiety="high",
    prior_knowledge="minimal",
    communication_style="passive",
    backstory="Retired housekeeper.",
)

SCENARIO = Scenario(
    test_name="Complete Blood Count",
    results="WBC: 11.2 x10^9/L",
    normal_range="4.5-11.0 x10^9/L",
    significance="Mildly elevated white blood cell count",
)


@pytest.fixture
def provider():
    return MockProvider(delay=0)


@pytest.fixture
def sim_static(provider):
    explainer = ExplainerAgent(provider, "default", "clinical", "static", SCENARIO)
    patient = PatientAgent(provider, "default", PERSONA)
    return Simulation(explainer, patient, "static")


@pytest.fixture
def sim_dialog(provider):
    explainer = ExplainerAgent(provider, "default", "analogy", "dialog", SCENARIO)
    patient = PatientAgent(provider, "default", PERSONA)
    return Simulation(explainer, patient, "dialog")


# ── State machine tests ──────────────────────────────────────────────────────


def test_initial_state_is_idle(sim_static):
    assert sim_static.state == SimulationStatus.IDLE


@pytest.mark.asyncio
async def test_run_completes(sim_static):
    trace = await sim_static.run()
    assert sim_static.state == SimulationStatus.COMPLETED
    assert isinstance(trace, AgentTrace)


@pytest.mark.asyncio
async def test_static_produces_2_turns(sim_static):
    trace = await sim_static.run()
    assert len(trace.steps) == 2


@pytest.mark.asyncio
async def test_dialog_produces_8_turns(sim_dialog):
    trace = await sim_dialog.run()
    assert len(trace.steps) == 8


@pytest.mark.asyncio
async def test_alternating_agents(sim_dialog):
    trace = await sim_dialog.run()
    for i, step in enumerate(trace.steps):
        expected = "ExplainerAgent" if i % 2 == 0 else "PatientAgent"
        assert step.agent_type == expected, f"Step {i}: expected {expected}, got {step.agent_type}"


@pytest.mark.asyncio
async def test_step_executes_one_turn(sim_static):
    step = await sim_static.step()
    assert isinstance(step, AgentStep)
    assert step.agent_type == "ExplainerAgent"
    assert sim_static.turn == 1
    assert len(sim_static.trace.steps) == 1


@pytest.mark.asyncio
async def test_step_from_idle(sim_static):
    assert sim_static.state == SimulationStatus.IDLE
    await sim_static.step()
    # After one step with more turns remaining → PAUSED
    assert sim_static.state == SimulationStatus.PAUSED


@pytest.mark.asyncio
async def test_step_until_completed(sim_static):
    # static mode = 2 turns
    await sim_static.step()
    assert sim_static.state == SimulationStatus.PAUSED
    await sim_static.step()
    assert sim_static.state == SimulationStatus.COMPLETED
    assert len(sim_static.trace.steps) == 2


@pytest.mark.asyncio
async def test_step_past_max_raises(sim_static):
    await sim_static.step()
    await sim_static.step()
    with pytest.raises(RuntimeError, match="All turns completed"):
        await sim_static.step()


@pytest.mark.asyncio
async def test_stop_from_paused(sim_static):
    await sim_static.step()
    assert sim_static.state == SimulationStatus.PAUSED
    sim_static.stop()
    assert sim_static.state == SimulationStatus.COMPLETED


@pytest.mark.asyncio
async def test_pause_and_resume(provider):
    explainer = ExplainerAgent(provider, "default", "analogy", "dialog", SCENARIO)
    patient = PatientAgent(provider, "default", PERSONA)
    sim = Simulation(explainer, patient, "dialog")

    # Step through first two turns manually
    await sim.step()
    assert sim.state == SimulationStatus.PAUSED
    assert len(sim.trace.steps) == 1

    await sim.step()
    assert sim.state == SimulationStatus.PAUSED
    assert len(sim.trace.steps) == 2

    # Now resume via run() to finish the rest
    sim.resume()
    trace = await sim.run()
    assert sim.state == SimulationStatus.COMPLETED
    assert len(trace.steps) == 8


# ── Trace integrity tests ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_trace_has_timing(sim_static):
    trace = await sim_static.run()
    assert trace.duration_ms > 0
    for step in trace.steps:
        assert step.duration_ms >= 0
        assert step.started_at <= step.ended_at


@pytest.mark.asyncio
async def test_no_step_errors(sim_dialog):
    trace = await sim_dialog.run()
    for step in trace.steps:
        assert step.error is None


@pytest.mark.asyncio
async def test_step_outputs_are_nonempty(sim_static):
    trace = await sim_static.run()
    for step in trace.steps:
        assert len(step.output.strip()) > 0


@pytest.mark.asyncio
async def test_step_has_correct_agent_type(sim_static):
    trace = await sim_static.run()
    assert trace.steps[0].agent_type == "ExplainerAgent"
    assert trace.steps[1].agent_type == "PatientAgent"


# ── Streaming tests ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_streaming_yields_events(sim_static):
    events = []
    async for event_type, data in sim_static.run_streaming():
        events.append(event_type)

    assert events.count("turn_start") == 2
    assert events.count("turn_end") == 2
    assert events.count("done") == 1
    assert events.count("token") > 0


@pytest.mark.asyncio
async def test_run_streaming_produces_trace(sim_static):
    async for _ in sim_static.run_streaming():
        pass

    assert sim_static.state == SimulationStatus.COMPLETED
    assert len(sim_static.trace.steps) == 2


@pytest.mark.asyncio
async def test_streaming_tokens_match_output(provider):
    explainer = ExplainerAgent(provider, "default", "clinical", "static", SCENARIO)
    patient = PatientAgent(provider, "default", PERSONA)
    sim = Simulation(explainer, patient, "static")

    turn_tokens: list[list[str]] = []
    current_tokens: list[str] = []

    async for event_type, data in sim.run_streaming():
        if event_type == "turn_start":
            current_tokens = []
        elif event_type == "token":
            current_tokens.append(data)
        elif event_type == "turn_end":
            turn_tokens.append(current_tokens)

    # Tokens for each turn should reconstruct the step output
    for i, tokens in enumerate(turn_tokens):
        assert "".join(tokens) == sim.trace.steps[i].output


@pytest.mark.asyncio
async def test_streaming_alternates_roles(sim_static):
    roles = []
    async for event_type, data in sim_static.run_streaming():
        if event_type == "turn_start":
            roles.append(data.role)

    assert roles == ["explainer", "patient"]


@pytest.mark.asyncio
async def test_streaming_typed_events(sim_static):
    start_events = []
    end_events = []
    async for event_type, data in sim_static.run_streaming():
        if event_type == "turn_start":
            assert isinstance(data, TurnStartEvent)
            start_events.append(data)
        elif event_type == "turn_end":
            assert isinstance(data, TurnEndEvent)
            end_events.append(data)

    assert len(start_events) == 2
    assert start_events[0].role == "explainer"
    assert start_events[0].turn == 0
    assert start_events[1].role == "patient"
    assert start_events[1].turn == 1

    assert len(end_events) == 2
    assert end_events[0].role == "explainer"
    assert end_events[0].turn == 0
    assert end_events[1].role == "patient"
    assert end_events[1].turn == 1
