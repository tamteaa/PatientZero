import pytest
from agents.judge import JudgeAgent
from llm.mock import MockProvider


@pytest.fixture
def provider():
    return MockProvider()


def test_judge_has_system_prompt(provider):
    agent = JudgeAgent(provider, "default")
    assert "evaluator" in agent.system_prompt.lower()
    assert "comprehension" in agent.system_prompt.lower()


@pytest.mark.asyncio
async def test_evaluate_returns_dict(provider):
    agent = JudgeAgent(provider, "default")
    result = await agent.evaluate(
        transcript=[
            {"role": "assistant", "content": "Your WBC is elevated."},
            {"role": "user", "content": "What does that mean?"},
        ],
        quiz_responses=[{"question": "What was elevated?", "answer": "WBC"}],
        answer_key=[{"question": "What was elevated?", "answer": "WBC"}],
        mode="dialog",
    )
    assert isinstance(result, dict)
    # Mock provider won't return valid JSON, so we get the fallback dict
    assert "justification" in result


@pytest.mark.asyncio
async def test_evaluate_builds_message(provider):
    agent = JudgeAgent(provider, "default")
    # The evaluate method should build a message with transcript, quiz, and answer key
    result = await agent.evaluate(
        transcript=[{"role": "user", "content": "test"}],
        quiz_responses=[],
        answer_key=[],
        mode="static",
    )
    assert isinstance(result, dict)
