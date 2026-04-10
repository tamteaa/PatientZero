from dataclasses import asdict, dataclass
from enum import Enum

from core.types.judge_result import JudgeResult
from core.types.message import Message


class SeedingMode(str, Enum):
    """How candidate targets are scored during optimization."""
    HISTORICAL_FAILURES = "historical_failures"
    FRESH_TRIALS = "fresh_trials"


@dataclass(frozen=True)
class OptimizationMetric:
    """
    Weighted combination of judge score dimensions to optimize.
    Single-dimension example: {"comprehension_score": 1.0}
    """
    weights: dict[str, float]

    def score(self, judge_result: JudgeResult) -> float:
        total = 0.0
        for name, weight in self.weights.items():
            value = getattr(judge_result, name, None)
            if value is not None:
                total += weight * value
        return total


@dataclass(frozen=True)
class OptimizationConfig:
    """All tunable knobs for one optimize run."""
    metric: OptimizationMetric
    seeding_mode: SeedingMode = SeedingMode.HISTORICAL_FAILURES
    num_candidates: int = 5
    trials_per_candidate: int = 10
    worst_cases_k: int = 5  # how many failure cases to include in the signal


@dataclass(frozen=True)
class OptimizationTarget:
    """
    The thing being optimized — a set of named prompt strings that
    get co-optimized. Persisted per experiment.
    """
    id: str
    experiment_id: str
    kind: str                       # "doctor_prompts" | "doctor_and_patient" | ...
    prompts: dict[str, str]         # name → template
    created_at: str
    parent_id: str | None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class FailureCase:
    """One low-scoring simulation, carried as context for DSPy."""
    simulation_id: str
    scenario_name: str
    patient_traits: dict[str, str]
    transcript: list[Message]
    scores: dict[str, int]
    judge_justification: str


@dataclass(frozen=True)
class FeedbackSignal:
    """Aggregated evidence from recent sims — the input to optimization."""
    simulations_considered: int
    mean_scores: dict[str, float]
    worst_cases: list[FailureCase]


@dataclass(frozen=True)
class OptimizationRequest:
    current_target: OptimizationTarget
    signal: FeedbackSignal
    config: OptimizationConfig


@dataclass(frozen=True)
class CandidateScore:
    target: OptimizationTarget
    mean_score: float
    trial_count: int


@dataclass(frozen=True)
class OptimizationResult:
    new_target: OptimizationTarget
    baseline: CandidateScore
    candidates: list[CandidateScore]
    improvement: float

    def to_dict(self) -> dict:
        return {
            "new_target": self.new_target.to_dict(),
            "baseline": {
                "target_id": self.baseline.target.id,
                "mean_score": self.baseline.mean_score,
                "trial_count": self.baseline.trial_count,
            },
            "candidates": [
                {
                    "target_id": c.target.id,
                    "mean_score": c.mean_score,
                    "trial_count": c.trial_count,
                }
                for c in self.candidates
            ],
            "improvement": self.improvement,
        }
