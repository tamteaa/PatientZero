import os
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from core.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    """Provider for OpenAI-compatible APIs (OpenAI, Kimi, etc.)."""

    def __init__(self, api_key: str, base_url: str | None = None):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            default_headers={
                "User-Agent": "patientzero/1.0",
                "X-Client-Name": "patientzero",
            },
        )

    async def stream(self, messages: list[dict], model: str) -> AsyncGenerator[str, None]:
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )
        async for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
