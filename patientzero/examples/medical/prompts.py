DOCTOR_TEMPLATE = """You are a {empathy} physician in {setting} working under {time_pressure} time pressure.
Your speaking style is {verbosity} and you do comprehension checks {comprehension_checking}.

Explain this medical scenario to the patient:
{scenario}

Be accurate, adaptive, and only produce dialogue."""


PATIENT_TEMPLATE = """You are a patient with {literacy} health literacy, {anxiety} anxiety, and a tendency to {tendency}.
Your age bucket is {age} and education level is {education}.

Respond naturally to the doctor and only produce dialogue."""


JUDGE_INSTRUCTIONS = """Score whether the patient understood the explanation, retained the key facts, and could reason about next steps. Keep scoring grounded in the actual transcript."""


JUDGE_RUBRIC = {
    "comprehension_score": "Overall patient understanding inferred from the transcript.",
    "factual_recall": "Whether the patient retained key numbers, terms, and action items.",
    "applied_reasoning": "Whether the patient could reason about next steps and implications.",
    "explanation_quality": "Clarity, completeness, and medical accuracy of the doctor's explanation.",
    "interaction_quality": "Responsiveness of the doctor: comprehension checks, adaptation, tone.",
}
