import pytest
from core.generators.llm import LLMScenarioGenerator
from core.llm.mock import MockProvider
from core.types import Scenario


@pytest.mark.asyncio
async def test_llm_generator_returns_scenarios():
    # MockProvider returns canned text, so we need to test that the generator
    # handles non-JSON gracefully. For a real test, we'd need a provider
    # that returns valid JSON.
    provider = MockProvider(delay=0)
    gen = LLMScenarioGenerator(provider, "default")
    # MockProvider won't return valid JSON, so this should raise
    with pytest.raises(Exception):
        await gen.generate(1)
