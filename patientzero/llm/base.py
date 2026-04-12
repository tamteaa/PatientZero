from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator


class LLMProvider(ABC):
    @abstractmethod
    async def stream(self, messages: list[dict], model: str) -> AsyncGenerator[str, None]:
        """Yield text chunks as they are generated."""
