from core.agents.base import Agent
from core.llm.base import LLMProvider
from core.types import AgentProfile


class SimAgent(Agent):
    """A simulation agent configured by an AgentProfile and a system prompt."""

    def __init__(self, provider: LLMProvider, model: str, profile: AgentProfile, system_prompt: str):
        self.profile = profile
        super().__init__(provider, model, system_prompt)

    @property
    def agent_type(self) -> str:
        return self.profile.role.value
