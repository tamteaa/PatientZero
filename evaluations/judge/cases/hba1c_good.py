from core.types import Message, Transcript

LABEL = "HbA1c — good comprehension"
EXPECTED = {
    "comprehension_score": (70, 100),
    "factual_recall": (65, 100),
    "applied_reasoning": (65, 100),
    "explanation_quality": (75, 100),
    "interaction_quality": (70, 100),
}

TRANSCRIPT = Transcript(messages=[
    Message(
        role="assistant",
        content=(
            "Your HbA1c test came back at 6.1%. This is a measure of your average "
            "blood sugar over the past 2 to 3 months. A normal level is below 5.7%, "
            "pre-diabetes is 5.7 to 6.4%, and diabetes is 6.5% or higher. So your "
            "result puts you in the pre-diabetes range."
        ),
    ),
    Message(
        role="user",
        content="Pre-diabetes... does that mean I'm going to get diabetes?",
    ),
    Message(
        role="assistant",
        content=(
            "Not necessarily. Pre-diabetes means your blood sugar is higher than normal "
            "but hasn't reached the diabetes threshold yet. The good news is that "
            "lifestyle changes — like eating healthier, getting more exercise, and "
            "managing your weight — can prevent it from progressing to type 2 diabetes. "
            "Many people successfully reverse pre-diabetes with these changes."
        ),
    ),
    Message(
        role="user",
        content=(
            "OK that's reassuring. So if I eat better and exercise more I can keep it "
            "from getting worse. And 6.5% is when it becomes actual diabetes, right?"
        ),
    ),
])
