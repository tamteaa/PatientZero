"""High-literacy patient who engages deeply and challenges the doctor."""
from patientzero.types import Message, Transcript

LABEL = "BMP — high literacy, deep engagement"
EXPECTED = {
    "comprehension_score": (80, 100),
    "factual_recall": (80, 100),
    "applied_reasoning": (80, 100),
    "explanation_quality": (70, 100),
    "interaction_quality": (70, 100),
}

TRANSCRIPT = Transcript(messages=[
    Message(
        role="assistant",
        content=(
            "Your basic metabolic panel shows a few things. Your glucose is 118 mg/dL — "
            "normal fasting is 70 to 100, so that's elevated. Your creatinine is 1.4, "
            "slightly above the 0.6 to 1.2 normal range, which may suggest your kidneys "
            "aren't filtering as efficiently as they should. Sodium, potassium, and "
            "calcium are all within normal limits."
        ),
    ),
    Message(
        role="user",
        content=(
            "118 fasting glucose — is that pre-diabetic territory? And the creatinine "
            "at 1.4, what's my estimated GFR? I want to know how significant the "
            "kidney finding is."
        ),
    ),
    Message(
        role="assistant",
        content=(
            "Good questions. Yes, fasting glucose between 100 and 125 is considered "
            "pre-diabetic. I'd recommend an HbA1c to get a longer-term picture. "
            "Your eGFR calculates to about 58, which puts you in stage 3a CKD. "
            "That said, one reading isn't diagnostic — we'd want to repeat this in "
            "3 months and check for protein in your urine to see if it's a trend."
        ),
    ),
    Message(
        role="user",
        content=(
            "Stage 3a — so mildly decreased function. I understand the single reading "
            "caveat. For the glucose, I'd like to do the HbA1c. And presumably we should "
            "look at whether the kidney finding and the glucose are related — could this "
            "be early diabetic nephropathy, or is that premature to speculate?"
        ),
    ),
])
