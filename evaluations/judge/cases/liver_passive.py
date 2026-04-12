"""Patient asks zero questions, gives minimal responses."""
from patientzero.types import Message, Transcript

LABEL = "Liver panel — passive patient, no questions"
EXPECTED = {
    "comprehension_score": (10, 45),
    "factual_recall": (0, 30),
    "applied_reasoning": (0, 25),
    "explanation_quality": (60, 100),
    "interaction_quality": (30, 70),
}

TRANSCRIPT = Transcript(messages=[
    Message(
        role="assistant",
        content=(
            "Your liver function tests show elevated ALT at 85 — the normal range is "
            "7 to 56 units per liter. Your AST is also elevated at 62, where normal "
            "is 10 to 40. These enzymes leak into your blood when liver cells are "
            "damaged. Your bilirubin and albumin are both normal, which is encouraging. "
            "We should discuss possible causes — alcohol use, medications, fatty liver "
            "disease — and get an ultrasound to take a closer look."
        ),
    ),
    Message(
        role="user",
        content="OK.",
    ),
    Message(
        role="assistant",
        content=(
            "Do you have any questions about these results? I want to make sure "
            "you understand what the elevated enzymes mean and what our next steps are."
        ),
    ),
    Message(
        role="user",
        content="No, I think I'm fine. Just tell me what I need to do.",
    ),
])
