from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from core.llm.base import LLMProvider
from core.types import AgentStep, Message


class Agent:
    def __init__(self, provider: LLMProvider, model: str, system_prompt: str):
        self.provider = provider
        self.model = model
        self.system_prompt = system_prompt

    @property
    def agent_type(self) -> str:
        return type(self).__name__

    def _build_messages(self, messages: list[dict]) -> list[dict]:
        """Prepend system prompt to message history."""
        return [{"role": "system", "content": self.system_prompt}] + messages

    async def respond(self, messages: list[dict]) -> AgentStep:
        """Run the agent and return a step recording the invocation."""
        started_at = datetime.now(timezone.utc)
        input_messages = [Message(**m) for m in messages]

        error = None
        chunks: list[str] = []
        try:
            async for token in self.stream(messages):
                chunks.append(token)
        except Exception as e:
            error = str(e)

        output = "".join(chunks)
        ended_at = datetime.now(timezone.utc)
        duration_ms = (ended_at - started_at).total_seconds() * 1000

        return AgentStep(
            agent_type=self.agent_type,
            model=self.model,
            system_prompt=self.system_prompt,
            input_messages=input_messages,
            output=output,
            started_at=started_at,
            ended_at=ended_at,
            duration_ms=duration_ms,
            error=error,
        )

    async def stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        """Stream response tokens."""
        full_messages = self._build_messages(messages)
        async for token in self.provider.stream(full_messages, self.model):
            yield token
