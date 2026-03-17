import pytest
from core.agents.explainer import ExplainerAgent
from core.llm.mock import MockProvider
from core.types import AgentStep, Scenario

SCENARIO = Scenario(
    test_name="Complete Blood Count",
    results="WBC: 11.2 x10^9/L",
    normal_range="4.5-11.0 x10^9/L",
    significance="Mildly elevated white blood cell count",
)


@pytest.fixture
def provider():
    return MockProvider(delay=0)


def test_clinical_static_prompt(provider):
    agent = ExplainerAgent(provider, "default", "clinical", "static", SCENARIO)
    assert "Complete Blood Count" in agent.system_prompt
    assert "clinical" in agent.system_prompt.lower()


def test_clinical_dialog_prompt(provider):
    agent = ExplainerAgent(provider, "default", "clinical", "dialog", SCENARIO)
    assert "Complete Blood Count" in agent.system_prompt
    assert "comprehension" in agent.system_prompt.lower() or "understanding" in agent.system_prompt.lower()


def test_analogy_static_prompt(provider):
    agent = ExplainerAgent(provider, "default", "analogy", "static", SCENARIO)
    assert "Complete Blood Count" in agent.system_prompt
    assert "analog" in agent.system_prompt.lower()


def test_analogy_dialog_prompt(provider):
    agent = ExplainerAgent(provider, "default", "analogy", "dialog", SCENARIO)
    assert "Complete Blood Count" in agent.system_prompt
    assert "analog" in agent.system_prompt.lower()


def test_invalid_style_mode_raises(provider):
    with pytest.raises(ValueError, match="Invalid style/mode"):
        ExplainerAgent(provider, "default", "invalid", "static", SCENARIO)


def test_scenario_fields_in_prompt(provider):
    agent = ExplainerAgent(provider, "default", "clinical", "static", SCENARIO)
    assert "WBC: 11.2" in agent.system_prompt
    assert "4.5-11.0" in agent.system_prompt
    assert "Mildly elevated" in agent.system_prompt


@pytest.mark.asyncio
async def test_respond_returns_trace(provider):
    agent = ExplainerAgent(provider, "default", "clinical", "static", SCENARIO)
    trace = await agent.respond([{"role": "user", "content": "Explain my results"}])
    assert isinstance(trace, AgentStep)
    assert trace.agent_type == "ExplainerAgent"
    assert trace.model == "default"
    assert len(trace.output) > 0
    assert trace.duration_ms >= 0
    assert trace.error is None


@pytest.mark.asyncio
async def test_stream_yields_tokens(provider):
    agent = ExplainerAgent(provider, "default", "analogy", "dialog", SCENARIO)
    tokens = []
    async for token in agent.stream([{"role": "user", "content": "What does this mean?"}]):
        tokens.append(token)
    assert len(tokens) > 0
    trace = await agent.respond([{"role": "user", "content": "What does this mean?"}])
    assert "".join(tokens) == trace.output
