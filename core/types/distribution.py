import math
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Distribution:
    """Discrete distribution over string values. Weights must sum to ~1.0."""
    weights: dict[str, float]

    def __post_init__(self):
        total = sum(self.weights.values())
        if not math.isclose(total, 1.0, abs_tol=1e-3):
            raise ValueError(f"Distribution weights must sum to 1.0, got {total}")

    def sample(self) -> str:
        values = list(self.weights.keys())
        ws = list(self.weights.values())
        return random.choices(values, weights=ws, k=1)[0]

    @classmethod
    def from_dict(cls, d: dict) -> "Distribution":
        return cls(weights=dict(d["weights"]))


@dataclass(frozen=True)
class ConditionalDistribution:
    """P(child | parent). One Distribution per parent value."""
    by_parent: dict[str, Distribution]

    def sample(self, parent: str) -> str:
        if parent not in self.by_parent:
            raise KeyError(f"No conditional distribution for parent value {parent!r}")
        return self.by_parent[parent].sample()

    @classmethod
    def from_dict(cls, d: dict) -> "ConditionalDistribution":
        return cls(by_parent={k: Distribution.from_dict(v) for k, v in d["by_parent"].items()})


@dataclass(frozen=True)
class PatientDistribution:
    """
    Joint distribution for patient traits. Sampled via a causal chain:
        age → education → literacy → tendency
        age → anxiety
    """
    age: Distribution
    education_by_age: ConditionalDistribution
    literacy_by_education: ConditionalDistribution
    anxiety_by_age: ConditionalDistribution
    tendency_by_literacy: ConditionalDistribution

    @classmethod
    def from_dict(cls, d: dict) -> "PatientDistribution":
        return cls(
            age=Distribution.from_dict(d["age"]),
            education_by_age=ConditionalDistribution.from_dict(d["education_by_age"]),
            literacy_by_education=ConditionalDistribution.from_dict(d["literacy_by_education"]),
            anxiety_by_age=ConditionalDistribution.from_dict(d["anxiety_by_age"]),
            tendency_by_literacy=ConditionalDistribution.from_dict(d["tendency_by_literacy"]),
        )


@dataclass(frozen=True)
class DoctorDistribution:
    """
    Joint distribution for doctor traits. Sampled via a causal chain:
        setting → time_pressure → verbosity
        empathy → comprehension_checking
    """
    setting: Distribution
    time_pressure_by_setting: ConditionalDistribution
    verbosity_by_time_pressure: ConditionalDistribution
    empathy: Distribution
    comprehension_check_by_empathy: ConditionalDistribution

    @classmethod
    def from_dict(cls, d: dict) -> "DoctorDistribution":
        return cls(
            setting=Distribution.from_dict(d["setting"]),
            time_pressure_by_setting=ConditionalDistribution.from_dict(d["time_pressure_by_setting"]),
            verbosity_by_time_pressure=ConditionalDistribution.from_dict(d["verbosity_by_time_pressure"]),
            empathy=Distribution.from_dict(d["empathy"]),
            comprehension_check_by_empathy=ConditionalDistribution.from_dict(d["comprehension_check_by_empathy"]),
        )
