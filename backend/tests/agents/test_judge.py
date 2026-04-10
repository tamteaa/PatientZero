import pytest
from core.agents.judge import JudgeAgent
from core.llm.mock import MockProvider
from core.types import JudgeResult, Message, Transcript


@pytest.fixture
def provider():
    return MockProvider(delay=0)


def test_judge_has_system_prompt(provider):
    agent = JudgeAgent(provider, "default")
    assert "evaluator" in agent.system_prompt.lower()
    assert "comprehension" in agent.system_prompt.lower()


@pytest.mark.asyncio
async def test_evaluate_returns_judge_result(provider):
    agent = JudgeAgent(provider, "default")
    transcript = Transcript(messages=[
        Message(role="assistant", content="Your WBC is elevated."),
        Message(role="user", content="What does that mean?"),
    ])
    result = await agent.evaluate(transcript)
    assert isinstance(result, JudgeResult)
    assert result.model == "default"
    assert hasattr(result, "justification")


@pytest.mark.asyncio
async def test_evaluate_builds_message(provider):
    agent = JudgeAgent(provider, "default")
    transcript = Transcript(messages=[
        Message(role="user", content="test"),
    ])
    result = await agent.evaluate(transcript)
    assert isinstance(result, JudgeResult)
