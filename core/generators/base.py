from abc import ABC, abstractmethod

from core.types import Scenario


class ScenarioGenerator(ABC):
    @abstractmethod
    def generate(self, n: int = 1) -> list[Scenario]:
        """Generate n scenarios synchronously."""


class AsyncScenarioGenerator(ABC):
    @abstractmethod
    async def generate(self, n: int = 1) -> list[Scenario]:
        """Generate n scenarios asynchronously (e.g. via LLM)."""
