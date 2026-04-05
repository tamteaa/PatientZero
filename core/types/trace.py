from dataclasses import dataclass, field, asdict
from datetime import datetime

from core.types.message import Message
from core.types.transcript import Transcript


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
    def transcript(self) -> Transcript:
        """Build a Transcript from each step's output."""
        return Transcript(messages=[Message(role=s.agent_type, content=s.output) for s in self.steps])

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
