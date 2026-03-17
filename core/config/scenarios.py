from core.types import Scenario

SCENARIOS = [
    Scenario(
        test_name="Complete Blood Count (CBC)",
        results="WBC: 11.2 (H), RBC: 4.1, Hemoglobin: 10.8 (L), Hematocrit: 33%, Platelets: 245",
        normal_range="WBC: 4.5-11.0, RBC: 4.0-5.5, Hemoglobin: 12.0-16.0, Hematocrit: 36-46%, Platelets: 150-400",
        significance="Elevated WBC may indicate infection or inflammation. Low hemoglobin suggests possible anemia.",
        keywords=["blood", "wbc", "hemoglobin", "anemia", "white blood cell", "red blood cell"],
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
    ),
]
