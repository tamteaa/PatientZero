from abc import ABC, abstractmethod

from core.types import Scenario


class ScenarioGenerator(ABC):
    @abstractmethod
    async def generate(self, n: int = 1) -> list[Scenario]:
        """Generate n scenarios."""
