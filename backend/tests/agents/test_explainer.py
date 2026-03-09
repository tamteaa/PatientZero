import pytest
from agents.explainer import ExplainerAgent
from llm.mock import MockProvider

SCENARIO = {
    "test_name": "Complete Blood Count",
    "results": "WBC: 11.2 x10^9/L",
    "normal_range": "4.5-11.0 x10^9/L",
    "significance": "Mildly elevated white blood cell count",
}


@pytest.fixture
def provider():
    return MockProvider()


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
async def test_respond_returns_string(provider):
    agent = ExplainerAgent(provider, "default", "clinical", "static", SCENARIO)
    result = await agent.respond([{"role": "user", "content": "Explain my results"}])
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_stream_yields_tokens(provider):
    agent = ExplainerAgent(provider, "default", "analogy", "dialog", SCENARIO)
    tokens = []
    async for token in agent.stream([{"role": "user", "content": "What does this mean?"}]):
        tokens.append(token)
    assert len(tokens) > 0
    assert "".join(tokens) == await agent.respond([{"role": "user", "content": "What does this mean?"}])
