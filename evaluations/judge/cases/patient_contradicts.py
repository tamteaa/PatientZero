"""Patient contradicts the doctor with misinformation."""
from patientzero.types import Message, Transcript

LABEL = "HbA1c — patient contradicts doctor with misinformation"
EXPECTED = {
    "comprehension_score": (15, 50),
    "factual_recall": (10, 40),
    "applied_reasoning": (10, 45),
    "explanation_quality": (60, 100),
    "interaction_quality": (50, 90),
}

TRANSCRIPT = Transcript(messages=[
    Message(
        role="assistant",
        content=(
            "Your HbA1c is 7.2%, which is above the 6.5% diabetes threshold. "
            "This tells us your average blood sugar has been elevated over the past "
            "2-3 months. We need to discuss medication options and lifestyle changes "
            "to bring this down."
        ),
    ),
    Message(
        role="user",
        content=(
            "My neighbor said anything under 8 is fine and you don't need medicine "
            "for it. She's been diabetic for years and she manages just with cinnamon "
            "supplements. I think I'll try that first."
        ),
    ),
    Message(
        role="assistant",
        content=(
            "I understand your neighbor shared her experience, but the medical "
            "guidelines are clear: an HbA1c target of under 7% is recommended for "
            "most people with diabetes to prevent complications like nerve damage, "
            "kidney disease, and vision problems. Cinnamon has not been shown to "
            "reliably lower blood sugar. I'd strongly recommend starting with "
            "Metformin alongside diet and exercise changes."
        ),
    ),
    Message(
        role="user",
        content=(
            "I don't know... I really don't want to take pills. Let me try the "
            "natural route for a few months first and we'll see."
        ),
    ),
])
