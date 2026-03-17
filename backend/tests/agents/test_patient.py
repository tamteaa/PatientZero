import pytest
from core.agents.patient import PatientAgent
from core.llm.mock import MockProvider
from core.types import AgentStep, Persona

PERSONA = Persona(
    name="Maria Garcia",
    age="62",
    education="High school",
    literacy_level="low",
    anxiety="high",
    prior_knowledge="minimal",
    communication_style="passive",
    backstory="Maria is a retired housekeeper who has never had serious health issues before.",
)


@pytest.fixture
def provider():
    return MockProvider(delay=0)


def test_persona_in_prompt(provider):
    agent = PatientAgent(provider, "default", PERSONA)
    assert "Maria Garcia" in agent.system_prompt
    assert "62" in agent.system_prompt
    assert "High school" in agent.system_prompt
    assert "low" in agent.system_prompt
    assert "high" in agent.system_prompt
    assert "passive" in agent.system_prompt
    assert "retired housekeeper" in agent.system_prompt


@pytest.mark.asyncio
async def test_respond_returns_trace(provider):
    agent = PatientAgent(provider, "default", PERSONA)
    trace = await agent.respond([{"role": "user", "content": "Your blood count is slightly elevated."}])
    assert isinstance(trace, AgentStep)
    assert trace.agent_type == "PatientAgent"
    assert trace.model == "default"
    assert len(trace.output) > 0
    assert len(trace.input_messages) == 1
    assert trace.input_messages[0].content == "Your blood count is slightly elevated."
    assert trace.duration_ms >= 0
    assert trace.error is None
    assert trace.started_at <= trace.ended_at


@pytest.mark.asyncio
async def test_stream_yields_tokens(provider):
    agent = PatientAgent(provider, "default", PERSONA)
    tokens = []
    async for token in agent.stream([{"role": "user", "content": "Let me explain your results."}]):
        tokens.append(token)
    assert len(tokens) > 0
