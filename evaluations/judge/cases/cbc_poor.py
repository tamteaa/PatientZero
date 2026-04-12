from patientzero.types import Message, Transcript

LABEL = "CBC — poor comprehension (catastrophizing)"
EXPECTED = {
    "comprehension_score": (0, 45),
    "factual_recall": (0, 30),
    "applied_reasoning": (0, 40),
    "explanation_quality": (55, 100),
    "interaction_quality": (30, 70),
}

TRANSCRIPT = Transcript(messages=[
    Message(
        role="assistant",
        content=(
            "Your Complete Blood Count results show two things to pay attention to. "
            "First, your white blood cell count is 11.2, which is slightly above the "
            "normal range of 4.5 to 11.0. This can indicate your body is fighting an "
            "infection or there's some inflammation. Second, your hemoglobin is 10.8, "
            "below the normal range of 12.0 to 16.0. This suggests mild anemia. "
            "Your platelets at 245 are within normal range. This isn't an emergency "
            "but you should follow up with your doctor."
        ),
    ),
    Message(
        role="user",
        content=(
            "Oh no... so something is really wrong with my blood? I knew it. "
            "Should I go to the hospital right now?"
        ),
    ),
])
