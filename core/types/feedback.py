from dataclasses import asdict, dataclass

from core.types.message import Message


@dataclass(frozen=True)
class OptimizationTarget:
    """A versioned bundle of agent-name → prompt-template strings."""
    id: str
    experiment_id: str
    kind: str
    prompts: dict[str, str]
    created_at: str
    parent_id: str | None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class FeedbackTrace:
    """One completed simulation bundled for the feedback agent."""
    simulation_id: str
    profiles: dict[str, dict[str, str]]
    transcript: list[Message]
    scores: dict[str, float | None]
    justification: str

    def to_dict(self) -> dict:
        return {
            "simulation_id": self.simulation_id,
            "profiles": {k: dict(v) for k, v in self.profiles.items()},
            "transcript": [{"role": m.role, "content": m.content} for m in self.transcript],
            "scores": dict(self.scores),
            "justification": self.justification,
        }


@dataclass(frozen=True)
class OptimizationResult:
    new_target: OptimizationTarget
    previous_target: OptimizationTarget
    rationale: str
    traces_considered: int

    def to_dict(self) -> dict:
        return {
            "new_target": self.new_target.to_dict(),
            "previous_target": self.previous_target.to_dict(),
            "rationale": self.rationale,
            "traces_considered": self.traces_considered,
        }
