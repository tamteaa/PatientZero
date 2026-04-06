from core.types import Message, Transcript

LABEL = "Metformin — mixed comprehension"
EXPECTED = {
    "comprehension_score": (45, 80),
    "factual_recall": (50, 85),
    "applied_reasoning": (50, 85),
    "explanation_quality": (65, 100),
    "interaction_quality": (55, 100),
}

TRANSCRIPT = Transcript(messages=[
    Message(
        role="assistant",
        content=(
            "You've been prescribed Metformin to help manage your blood sugar. "
            "You'll start with 500mg once daily, taken with dinner. After two weeks, "
            "if you're tolerating it well, we'll increase to 500mg twice daily."
        ),
    ),
    Message(
        role="user",
        content="500mg with dinner, got it. What if I get side effects?",
    ),
    Message(
        role="assistant",
        content=(
            "Common side effects include nausea and diarrhea, but these usually improve "
            "after the first week or two as your body adjusts. However, if you experience "
            "severe stomach pain, muscle pain or weakness, difficulty breathing, or "
            "unusual fatigue, call your doctor immediately — those could be signs of a "
            "rare but serious reaction."
        ),
    ),
    Message(
        role="user",
        content="OK so some stomach stuff is normal at first but the serious stuff means call the doctor.",
    ),
])
