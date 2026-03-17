import asyncio
from collections.abc import AsyncGenerator

from core.llm.base import LLMProvider


class MockProvider(LLMProvider):
    def __init__(self, delay: float = 0.03):
        self.delay = delay

    async def stream(self, messages: list[dict], model: str) -> AsyncGenerator[str, None]:
        last_message = messages[-1]["content"] if messages else ""
        response = (
            f"[mock:{model}] This is a mock response to: \"{last_message}\". "
            "I'm a simulated LLM provider used for testing the chat interface. "
            "Once a real provider is configured, you'll get actual AI responses here."
        )
        for word in response.split():
            yield word + " "
            await asyncio.sleep(self.delay)
