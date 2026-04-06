from core.types import Message, Transcript

LABEL = "CBC — good comprehension"
EXPECTED = {
    "comprehension_score": (70, 100),
    "factual_recall": (65, 100),
    "applied_reasoning": (60, 100),
    "explanation_quality": (70, 100),
    "interaction_quality": (50, 100),
}

TRANSCRIPT = Transcript(messages=[
    Message(
        role="assistant",
        content=(
            "Your Complete Blood Count results show two things to pay attention to. "
            "First, your white blood cell count is 11.2, which is slightly above the "
            "normal range of 4.5 to 11.0. This can indicate your body is fighting an "
            "infection or there's some inflammation. It's not a sign of anything serious "
            "on its own. Second, your hemoglobin is 10.8, below the normal range of "
            "12.0 to 16.0. This suggests mild anemia, meaning your blood is carrying "
            "less oxygen than it should. Your platelets at 245 and red blood cells at "
            "4.1 are both within normal range. This isn't an emergency — you don't need "
            "to rush to the ER — but you should follow up with your doctor to discuss "
            "these results."
        ),
    ),
    Message(
        role="user",
        content=(
            "OK so my white blood cells are a little high which might mean infection, "
            "and my hemoglobin is low so I might be anemic. The other numbers are fine. "
            "I should see my doctor but it's not an emergency. Got it."
        ),
    ),
])
