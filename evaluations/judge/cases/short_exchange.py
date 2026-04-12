"""Very short exchange — only 1 doctor turn, 1 patient response."""
from patientzero.types import Message, Transcript

LABEL = "Potassium — minimal exchange (2 turns)"
EXPECTED = {
    "comprehension_score": (40, 80),
    "factual_recall": (30, 75),
    "applied_reasoning": (40, 85),
    "explanation_quality": (50, 85),
    "interaction_quality": (40, 80),
}

TRANSCRIPT = Transcript(messages=[
    Message(
        role="assistant",
        content=(
            "Your potassium level came back at 5.8 mEq/L. Normal is 3.5 to 5.0. "
            "High potassium can affect your heart rhythm, so we need to address this. "
            "Are you taking any potassium supplements or ACE inhibitors?"
        ),
    ),
    Message(
        role="user",
        content=(
            "5.8 — that's high? I do take lisinopril for my blood pressure. "
            "So that could be causing it?"
        ),
    ),
])
