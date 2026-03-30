from core.types import Scenario

SCENARIOS = [
    Scenario(
        test_name="Complete Blood Count (CBC)",
        results="WBC: 11.2 (H), RBC: 4.1, Hemoglobin: 10.8 (L), Hematocrit: 33%, Platelets: 245",
        normal_range="WBC: 4.5-11.0, RBC: 4.0-5.5, Hemoglobin: 12.0-16.0, Hematocrit: 36-46%, Platelets: 150-400",
        significance="Elevated WBC may indicate infection or inflammation. Low hemoglobin suggests possible anemia.",
        keywords=["blood", "wbc", "hemoglobin", "anemia", "white blood cell", "red blood cell"],
        quiz=[
            {
                "question": "What does it mean that your WBC count is elevated?",
                "answer": "It may indicate infection or inflammation. It is not typically a sign of cancer unless very high.",
            },
            {
                "question": "Your hemoglobin is low. What condition does this suggest?",
                "answer": "Anemia — the blood is carrying less oxygen than normal.",
            },
            {
                "question": "Are your platelet levels within the normal range?",
                "answer": "Yes, platelets at 245 are within the normal range of 150–400.",
            },
            {
                "question": "How urgent are these results — do you need to go to the emergency room?",
                "answer": "No emergency room needed. The results warrant a follow-up with a doctor but are not a medical emergency.",
            },
        ],
    ),
    Scenario(
        test_name="Hemoglobin A1c (HbA1c)",
        results="HbA1c: 6.1%",
        normal_range="Normal: below 5.7%, Pre-diabetes: 5.7-6.4%, Diabetes: 6.5% or higher",
        significance=(
            "An HbA1c of 6.1% indicates pre-diabetes. Blood sugar levels have been elevated "
            "over the past 2-3 months. Lifestyle changes can prevent progression to type 2 diabetes."
        ),
        keywords=["hba1c", "blood sugar", "pre-diabetes", "diabetes", "glucose", "lifestyle"],
        quiz=[
            {
                "question": "What does your HbA1c result of 6.1% mean for your health?",
                "answer": "It indicates pre-diabetes — blood sugar has been elevated over the past 2–3 months but has not yet reached the diabetes threshold.",
            },
            {
                "question": "What HbA1c value would indicate a diabetes diagnosis?",
                "answer": "6.5% or higher.",
            },
            {
                "question": "How long a time period does your HbA1c result reflect?",
                "answer": "The past 2–3 months.",
            },
            {
                "question": "What can you do to prevent pre-diabetes from becoming type 2 diabetes?",
                "answer": "Lifestyle changes such as improved diet, increased physical activity, and weight management.",
            },
        ],
    ),
    Scenario(
        test_name="Metformin Prescription",
        results=(
            "Starting dose: 500mg once daily with dinner. Increase to 500mg twice daily "
            "after 2 weeks if tolerated. Maximum dose: 2000mg/day."
        ),
        normal_range="Target fasting blood glucose: 80-130 mg/dL. Target HbA1c: below 7%.",
        significance=(
            "Common side effects: nausea, diarrhea (usually improve after 1-2 weeks). "
            "Call doctor immediately if: severe stomach pain, muscle pain/weakness, "
            "difficulty breathing, or unusual fatigue."
        ),
        keywords=["metformin", "dose", "500mg", "side effect", "medication", "blood sugar"],
        quiz=[
            {
                "question": "What is your starting dose of Metformin and when should you take it?",
                "answer": "500mg once daily with dinner.",
            },
            {
                "question": "After two weeks, how should your dose change if you tolerate it well?",
                "answer": "Increase to 500mg twice daily.",
            },
            {
                "question": "Name one common side effect of Metformin and when it typically improves.",
                "answer": "Nausea or diarrhea, usually improving after 1–2 weeks.",
            },
            {
                "question": "Name one symptom that means you should call your doctor immediately.",
                "answer": "Severe stomach pain, muscle pain or weakness, difficulty breathing, or unusual fatigue.",
            },
        ],
    ),
]
