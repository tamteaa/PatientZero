from dataclasses import dataclass, asdict


@dataclass
class JudgeResult:
    model: str
    comprehension_score: float | None
    factual_recall: float | None
    applied_reasoning: float | None
    explanation_quality: float | None
    interaction_quality: float | None
    confidence_comprehension_gap: str | None
    justification: str | None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "JudgeResult":
        return cls(
            model=data.get("model", ""),
            comprehension_score=data.get("comprehension_score"),
            factual_recall=data.get("factual_recall"),
            applied_reasoning=data.get("applied_reasoning"),
            explanation_quality=data.get("explanation_quality"),
            interaction_quality=data.get("interaction_quality"),
            confidence_comprehension_gap=data.get("confidence_comprehension_gap"),
            justification=data.get("justification"),
        )
