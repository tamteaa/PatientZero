from __future__ import annotations

from dataclasses import asdict, dataclass

_LEGACY_SCORE_KEYS = (
    "comprehension_score",
    "factual_recall",
    "applied_reasoning",
    "explanation_quality",
    "interaction_quality",
)


@dataclass
class JudgeResult:
    model: str
    scores: dict[str, float | None]
    justification: str | None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "JudgeResult":
        if "scores" in data and isinstance(data["scores"], dict):
            scores = dict(data["scores"])
        else:
            scores = {
                key: data.get(key)
                for key in _LEGACY_SCORE_KEYS
                if key in data
            }
        return cls(
            model=data.get("model", ""),
            scores=scores,
            justification=data.get("justification"),
        )

    def __getattr__(self, name: str):
        if name in self.scores:
            return self.scores.get(name)
        if name == "confidence_comprehension_gap":
            return None
        raise AttributeError(name)
