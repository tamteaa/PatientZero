"""
Baseline patient and doctor distributions for the medical example.

Patient causal chain:
    age → education → literacy → tendency
    age → anxiety
    age → scenario          # which test result they're showing up with

Doctor causal chain:
    setting → time_pressure → verbosity
    empathy → comprehension_checking
"""

from patientzero.distribution import Conditional, Distribution


_CBC_ANEMIA = (
    "Medical Test: Complete Blood Count (CBC)\n"
    "Results: WBC: 11.2 (H), RBC: 4.1, Hemoglobin: 10.8 (L), Hematocrit: 33%, Platelets: 245\n"
    "Normal Range: WBC: 4.5-11.0, RBC: 4.0-5.5, Hemoglobin: 12.0-16.0, Hematocrit: 36-46%, Platelets: 150-400\n"
    "Clinical Significance: Elevated WBC may indicate infection or inflammation. Low hemoglobin suggests possible anemia."
)

_HBA1C_PREDIABETES = (
    "Medical Test: Hemoglobin A1c (HbA1c)\n"
    "Results: HbA1c: 6.1%\n"
    "Normal Range: Normal: below 5.7%, Pre-diabetes: 5.7-6.4%, Diabetes: 6.5% or higher\n"
    "Clinical Significance: An HbA1c of 6.1% indicates pre-diabetes. Blood sugar has been elevated over the past 2-3 months."
)

_METFORMIN_RX = (
    "Medical Test: Metformin Prescription\n"
    "Starting dose: 500mg once daily with dinner. Increase to 500mg twice daily after 2 weeks if tolerated. Maximum dose: 2000mg/day.\n"
    "Common side effects: nausea, diarrhea. Seek care for severe stomach pain, muscle pain, difficulty breathing, or unusual fatigue."
)


US_ADULT_PATIENT = Distribution(
    age={"young": 0.28, "middle": 0.35, "older": 0.25, "senior": 0.12},
    education=Conditional(
        "age",
        {
            "young": {
                "less than high school": 0.08,
                "high school diploma": 0.28,
                "some college": 0.30,
                "bachelor's degree": 0.24,
                "graduate degree": 0.10,
            },
            "middle": {
                "less than high school": 0.10,
                "high school diploma": 0.28,
                "some college": 0.26,
                "bachelor's degree": 0.24,
                "graduate degree": 0.12,
            },
            "older": {
                "less than high school": 0.14,
                "high school diploma": 0.32,
                "some college": 0.22,
                "bachelor's degree": 0.20,
                "graduate degree": 0.12,
            },
            "senior": {
                "less than high school": 0.22,
                "high school diploma": 0.38,
                "some college": 0.18,
                "bachelor's degree": 0.14,
                "graduate degree": 0.08,
            },
        },
    ),
    literacy=Conditional(
        "education",
        {
            "less than high school": {"low": 0.75, "moderate": 0.22, "high": 0.03},
            "high school diploma": {"low": 0.40, "moderate": 0.48, "high": 0.12},
            "some college": {"low": 0.20, "moderate": 0.55, "high": 0.25},
            "bachelor's degree": {"low": 0.08, "moderate": 0.42, "high": 0.50},
            "graduate degree": {"low": 0.03, "moderate": 0.27, "high": 0.70},
        },
    ),
    anxiety=Conditional(
        "age",
        {
            "young": {"low": 0.35, "moderate": 0.45, "high": 0.20},
            "middle": {"low": 0.30, "moderate": 0.42, "high": 0.28},
            "older": {"low": 0.25, "moderate": 0.38, "high": 0.37},
            "senior": {"low": 0.20, "moderate": 0.35, "high": 0.45},
        },
    ),
    tendency=Conditional(
        "literacy",
        {
            "low": {
                "agrees even when confused": 0.50,
                "asks few questions": 0.30,
                "defers to authority": 0.20,
            },
            "moderate": {
                "asks clarifying questions": 0.40,
                "agrees mostly but pushes back sometimes": 0.35,
                "follows along but misses nuance": 0.25,
            },
            "high": {
                "asks direct targeted questions": 0.45,
                "challenges assumptions": 0.30,
                "wants data and specifics": 0.25,
            },
        },
    ),
    scenario=Conditional(
        "age",
        {
            "young": {_CBC_ANEMIA: 0.55, _HBA1C_PREDIABETES: 0.30, _METFORMIN_RX: 0.15},
            "middle": {_CBC_ANEMIA: 0.35, _HBA1C_PREDIABETES: 0.40, _METFORMIN_RX: 0.25},
            "older": {_CBC_ANEMIA: 0.25, _HBA1C_PREDIABETES: 0.40, _METFORMIN_RX: 0.35},
            "senior": {_CBC_ANEMIA: 0.20, _HBA1C_PREDIABETES: 0.35, _METFORMIN_RX: 0.45},
        },
    ),
)


US_BASELINE_DOCTOR = Distribution(
    setting={
        "primary care": 0.45,
        "hospital medicine": 0.20,
        "emergency medicine": 0.15,
        "specialty clinic": 0.20,
    },
    time_pressure=Conditional(
        "setting",
        {
            "primary care": {"low": 0.30, "moderate": 0.50, "high": 0.20},
            "hospital medicine": {"low": 0.20, "moderate": 0.40, "high": 0.40},
            "emergency medicine": {"low": 0.05, "moderate": 0.25, "high": 0.70},
            "specialty clinic": {"low": 0.40, "moderate": 0.45, "high": 0.15},
        },
    ),
    verbosity=Conditional(
        "time_pressure",
        {
            "low": {"terse": 0.10, "moderate": 0.40, "thorough": 0.50},
            "moderate": {"terse": 0.25, "moderate": 0.55, "thorough": 0.20},
            "high": {"terse": 0.60, "moderate": 0.35, "thorough": 0.05},
        },
    ),
    empathy={"low": 0.20, "moderate": 0.45, "high": 0.35},
    comprehension_checking=Conditional(
        "empathy",
        {
            "low": {"rarely": 0.60, "sometimes": 0.35, "always": 0.05},
            "moderate": {"rarely": 0.20, "sometimes": 0.55, "always": 0.25},
            "high": {"rarely": 0.05, "sometimes": 0.35, "always": 0.60},
        },
    ),
)
