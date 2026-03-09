import pytest
from llm.mock import MockProvider


@pytest.mark.asyncio
async def test_mock_streams_tokens():
    provider = MockProvider()
    tokens = []
    async for token in provider.stream([{"role": "user", "content": "Hi"}], "default"):
        tokens.append(token)
    assert len(tokens) > 0
    full = "".join(tokens)
    assert len(full) > 0


@pytest.mark.asyncio
async def test_mock_includes_user_message():
    provider = MockProvider()
    tokens = []
    async for token in provider.stream([{"role": "user", "content": "test message"}], "default"):
        tokens.append(token)
    full = "".join(tokens)
    assert "test message" in full


@pytest.mark.asyncio
async def test_mock_includes_model_name():
    provider = MockProvider()
    tokens = []
    async for token in provider.stream([{"role": "user", "content": "Hi"}], "mymodel"):
        tokens.append(token)
    full = "".join(tokens)
    assert "mock:mymodel" in full
