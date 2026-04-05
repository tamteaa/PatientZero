import pytest
from core.agents.sim_agent import SimAgent
from core.agents.prompts import build_patient_prompt
from core.llm.mock import MockProvider
from core.types import AgentProfile, AgentStep, Role

PROFILE = AgentProfile(name="Test Patient", role=Role.PATIENT, traits={"literacy": "low", "anxiety": "high"}, backstory="Test patient.")


@pytest.fixture
def provider():
    return MockProvider(delay=0)


def test_patient_prompt_has_profile(provider):
    prompt = build_patient_prompt(PROFILE)
    agent = SimAgent(provider, "default", PROFILE, prompt)
    assert "Test Patient" in agent.system_prompt
    assert "low" in agent.system_prompt


@pytest.mark.asyncio
async def test_respond_returns_step(provider):
    prompt = build_patient_prompt(PROFILE)
    agent = SimAgent(provider, "default", PROFILE, prompt)
    step = await agent.respond([{"role": "user", "content": "Your WBC is elevated."}])
    assert isinstance(step, AgentStep)
    assert step.agent_type == "patient"
    assert len(step.output) > 0


@pytest.mark.asyncio
async def test_stream_yields_tokens(provider):
    prompt = build_patient_prompt(PROFILE)
    agent = SimAgent(provider, "default", PROFILE, prompt)
    tokens = []
    async for token in agent.stream([{"role": "user", "content": "Hello"}]):
        tokens.append(token)
    assert len(tokens) > 0
