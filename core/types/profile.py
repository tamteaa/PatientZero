from dataclasses import dataclass, field

from core.types.enums import Role


@dataclass
class AgentProfile:
    name: str
    role: Role
    traits: dict[str, str] = field(default_factory=dict)
    backstory: str = ""
