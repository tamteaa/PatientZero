from collections.abc import AsyncGenerator
from llm.base import LLMProvider


class Agent:
    def __init__(self, provider: LLMProvider, model: str, system_prompt: str):
        self.provider = provider
        self.model = model
        self.system_prompt = system_prompt

    def _build_messages(self, messages: list[dict]) -> list[dict]:
        """Prepend system prompt to message history."""
        return [{"role": "system", "content": self.system_prompt}] + messages

    async def respond(self, messages: list[dict]) -> str:
        """Get full (non-streaming) response by collecting all streamed tokens."""
        chunks = []
        async for token in self.stream(messages):
            chunks.append(token)
        return "".join(chunks)

    async def stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        """Stream response tokens."""
        full_messages = self._build_messages(messages)
        async for token in self.provider.stream(full_messages, self.model):
            yield token
