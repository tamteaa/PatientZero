import pytest
from agents.patient import PatientAgent
from llm.mock import MockProvider

PERSONA = {
    "name": "Maria Garcia",
    "age": 62,
    "education": "High school",
    "literacy_level": "low",
    "anxiety": "high",
    "prior_knowledge": "minimal",
    "communication_style": "passive",
    "backstory": "Maria is a retired housekeeper who has never had serious health issues before.",
}


@pytest.fixture
def provider():
    return MockProvider()


def test_persona_in_prompt(provider):
    agent = PatientAgent(provider, "default", PERSONA)
    assert "Maria Garcia" in agent.system_prompt
    assert "62" in agent.system_prompt
    assert "High school" in agent.system_prompt
    assert "low" in agent.system_prompt
    assert "high" in agent.system_prompt
    assert "passive" in agent.system_prompt
    assert "retired housekeeper" in agent.system_prompt


def test_default_persona_values(provider):
    agent = PatientAgent(provider, "default", {})
    assert "Patient" in agent.system_prompt
    assert "moderate" in agent.system_prompt


@pytest.mark.asyncio
async def test_respond_returns_string(provider):
    agent = PatientAgent(provider, "default", PERSONA)
    result = await agent.respond([{"role": "user", "content": "Your blood count is slightly elevated."}])
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_stream_yields_tokens(provider):
    agent = PatientAgent(provider, "default", PERSONA)
    tokens = []
    async for token in agent.stream([{"role": "user", "content": "Let me explain your results."}]):
        tokens.append(token)
    assert len(tokens) > 0
