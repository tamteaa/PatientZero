from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum


@dataclass
class Persona:
    name: str
    age: str
    education: str
    literacy_level: str
    anxiety: str
    prior_knowledge: str
    communication_style: str
    backstory: str


@dataclass
class Scenario:
    test_name: str
    results: str
    normal_range: str
    significance: str
    keywords: list[str] = field(default_factory=list)
    quiz: list[dict] = field(default_factory=list)


class SimulationStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class Message:
    role: str
    content: str


@dataclass
class SimulationState:
    """Full state of a simulation at any point in time."""

    status: SimulationStatus
    simulation_id: str | None = None
    config: dict | None = None         # serialized SimulationConfig
    messages: list[Message] = field(default_factory=list)
    current_turn: int = 0
    error: str | None = None


@dataclass
class TurnStartEvent:
    role: str     # "explainer" | "patient"
    turn: int     # 0-based index


@dataclass
class TurnEndEvent:
    role: str     # "explainer" | "patient"
    turn: int


@dataclass
class AgentStep:
    """Record of a single agent invocation (one LLM call)."""

    agent_type: str                    # class name, e.g. "PatientAgent"
    model: str                         # provider:model string
    system_prompt: str                 # full system prompt used
    input_messages: list[Message]      # conversation history sent (excludes system prompt)
    output: str                        # full response text
    started_at: datetime               # UTC
    ended_at: datetime                 # UTC
    duration_ms: float                 # wall-clock milliseconds
    error: str | None = None           # non-None if the call failed


@dataclass
class AgentTrace:
    """Full trajectory of a multi-step agent interaction."""

    steps: list[AgentStep] = field(default_factory=list)
    started_at: datetime | None = None
    ended_at: datetime | None = None

    def add(self, step: AgentStep) -> None:
        """Append a step and update trace timing."""
        self.steps.append(step)
        if self.started_at is None or step.started_at < self.started_at:
            self.started_at = step.started_at
        if self.ended_at is None or step.ended_at > self.ended_at:
            self.ended_at = step.ended_at

    @property
    def duration_ms(self) -> float:
        if self.started_at and self.ended_at:
            return (self.ended_at - self.started_at).total_seconds() * 1000
        return 0.0

    @property
    def transcript(self) -> list[Message]:
        """Flat list of (role, content) from each step's output."""
        return [Message(role=s.agent_type, content=s.output) for s in self.steps]

    def to_dict(self) -> dict:
        """JSON-serializable dict."""
        d = asdict(self)
        if self.started_at:
            d["started_at"] = self.started_at.isoformat()
        if self.ended_at:
            d["ended_at"] = self.ended_at.isoformat()
        for step in d["steps"]:
            step["started_at"] = step["started_at"].isoformat() if isinstance(step["started_at"], datetime) else step["started_at"]
            step["ended_at"] = step["ended_at"].isoformat() if isinstance(step["ended_at"], datetime) else step["ended_at"]
        d["duration_ms"] = self.duration_ms
        return d
