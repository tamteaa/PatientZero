from core.types import Scenario

SCENARIOS = [
    Scenario(
        name="CBC - Elevated WBC / Low Hemoglobin",
        description=(
            "Medical Test: Complete Blood Count (CBC)\n"
            "Results: WBC: 11.2 (H), RBC: 4.1, Hemoglobin: 10.8 (L), Hematocrit: 33%, Platelets: 245\n"
            "Normal Range: WBC: 4.5-11.0, RBC: 4.0-5.5, Hemoglobin: 12.0-16.0, Hematocrit: 36-46%, Platelets: 150-400\n"
            "Clinical Significance: Elevated WBC may indicate infection or inflammation. Low hemoglobin suggests possible anemia."
        ),
    ),
    Scenario(
        name="HbA1c - Pre-diabetes",
        description=(
            "Medical Test: Hemoglobin A1c (HbA1c)\n"
            "Results: HbA1c: 6.1%\n"
            "Normal Range: Normal: below 5.7%, Pre-diabetes: 5.7-6.4%, Diabetes: 6.5% or higher\n"
            "Clinical Significance: An HbA1c of 6.1% indicates pre-diabetes. Blood sugar levels have been "
            "elevated over the past 2-3 months. Lifestyle changes can prevent progression to type 2 diabetes."
        ),
    ),
    Scenario(
        name="Metformin Prescription",
        description=(
            "Medical Test: Metformin Prescription\n"
            "Starting dose: 500mg once daily with dinner. Increase to 500mg twice daily after 2 weeks if tolerated. "
            "Maximum dose: 2000mg/day.\n"
            "Target fasting blood glucose: 80-130 mg/dL. Target HbA1c: below 7%.\n"
            "Common side effects: nausea, diarrhea (usually improve after 1-2 weeks). "
            "Call doctor immediately if: severe stomach pain, muscle pain/weakness, "
            "difficulty breathing, or unusual fatigue."
        ),
    ),
]
