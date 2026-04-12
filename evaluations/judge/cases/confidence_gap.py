"""Patient sounds confident but reveals incorrect understanding. Doctor doesn't catch it."""
from patientzero.types import Message, Transcript

LABEL = "Thyroid — confident but wrong (confidence-comprehension gap)"
EXPECTED = {
    "comprehension_score": (10, 45),
    "factual_recall": (10, 40),
    "applied_reasoning": (5, 35),
    "explanation_quality": (55, 100),
    "interaction_quality": (20, 65),
}

TRANSCRIPT = Transcript(messages=[
    Message(
        role="assistant",
        content=(
            "Your thyroid panel shows your TSH is elevated at 8.2. The normal range "
            "is 0.4 to 4.0. This suggests your thyroid is underactive — a condition "
            "called hypothyroidism. Your Free T4 is also low at 0.6, which confirms "
            "the thyroid isn't producing enough hormone. This can cause fatigue, weight "
            "gain, and feeling cold. We'll likely start you on levothyroxine to replace "
            "the missing thyroid hormone."
        ),
    ),
    Message(
        role="user",
        content=(
            "Right, so my thyroid is overactive — that's why I've been so tired. "
            "The TSH being high means it's working too hard. Makes sense. "
            "So the levothyroxine will slow it down? That's fine, I'll take it. "
            "I totally get it."
        ),
    ),
])
