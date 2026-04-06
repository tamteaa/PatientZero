import pytest
from core.agents.sim_agent import SimAgent
from core.agents.prompts import build_doctor_prompt
from core.llm.mock import MockProvider
from core.types import AgentProfile, AgentStep, Role, Scenario

PROFILE = AgentProfile(name="Dr. Test", role=Role.DOCTOR, traits={"empathy": "high"}, backstory="Test doctor.")
SCENARIO = Scenario(name="CBC", description="Medical Test: Complete Blood Count\nResults: WBC: 11.2\nNormal Range: 4.5-11.0\nClinical Significance: Elevated WBC")


@pytest.fixture
def provider():
    return MockProvider(delay=0)


def test_doctor_prompt(provider):
    prompt = build_doctor_prompt(PROFILE, SCENARIO)
    agent = SimAgent(provider, "default", PROFILE, prompt)
    assert "Complete Blood Count" in agent.system_prompt
    assert "Dr. Test" in agent.system_prompt


def test_scenario_fields_in_prompt(provider):
    prompt = build_doctor_prompt(PROFILE, SCENARIO)
    assert "WBC: 11.2" in prompt
    assert "4.5-11.0" in prompt
    assert "Elevated WBC" in prompt


@pytest.mark.asyncio
async def test_respond_returns_step(provider):
    prompt = build_doctor_prompt(PROFILE, SCENARIO)
    agent = SimAgent(provider, "default", PROFILE, prompt)
    step = await agent.respond([{"role": "user", "content": "Explain my results"}])
    assert isinstance(step, AgentStep)
    assert step.agent_type == "doctor"
    assert len(step.output) > 0


@pytest.mark.asyncio
async def test_stream_yields_tokens(provider):
    prompt = build_doctor_prompt(PROFILE, SCENARIO)
    agent = SimAgent(provider, "default", PROFILE, prompt)
    tokens = []
    async for token in agent.stream([{"role": "user", "content": "What does this mean?"}]):
        tokens.append(token)
    assert len(tokens) > 0
