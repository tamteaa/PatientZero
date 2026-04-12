"""Doctor gives a vague, jargon-heavy explanation with no structure. Patient is lost."""
from patientzero.types import Message, Transcript

LABEL = "Lipid panel — bad doctor explanation"
EXPECTED = {
    "comprehension_score": (0, 40),
    "factual_recall": (0, 25),
    "applied_reasoning": (0, 30),
    "explanation_quality": (0, 35),
    "interaction_quality": (0, 35),
}

TRANSCRIPT = Transcript(messages=[
    Message(
        role="assistant",
        content=(
            "So your lipids came back. Total cholesterol 245, LDL 165, HDL 38, "
            "triglycerides 210. The LDL-to-HDL ratio is suboptimal and your "
            "atherogenic index suggests elevated cardiovascular risk stratification. "
            "We should consider statin therapy given your Framingham score."
        ),
    ),
    Message(
        role="user",
        content="I... what? What does any of that mean? Is my cholesterol bad?",
    ),
    Message(
        role="assistant",
        content=(
            "Yes, your LDL is above the 130 threshold and your HDL is below "
            "the protective 40 cutoff. Combined with hypertriglyceridemia at 210, "
            "your non-HDL cholesterol of 207 puts you in a higher risk category. "
            "I'll write you a prescription."
        ),
    ),
    Message(
        role="user",
        content=(
            "OK... so I need medicine? I don't really understand the numbers "
            "but I guess if you say so."
        ),
    ),
])
