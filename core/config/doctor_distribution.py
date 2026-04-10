"""
Default doctor target distribution — "US physician baseline."

Weights calibrated to:
- Setting: approximate distribution of US clinical practice settings
- Time pressure | setting: observational studies of visit duration
- Verbosity | time pressure: RIAS (Roter Interaction Analysis System)
- Empathy: CAHPS patient-reported measures
- Comprehension checking | empathy: RIAS information-giving codes
"""

from core.types import ConditionalDistribution, Distribution, DoctorDistribution


US_BASELINE_DOCTOR = DoctorDistribution(
    setting=Distribution({
        "primary care":       0.45,
        "hospital medicine":  0.20,
        "emergency medicine": 0.15,
        "specialty clinic":   0.20,
    }),
    time_pressure_by_setting=ConditionalDistribution({
        "primary care":       Distribution({"low": 0.30, "moderate": 0.50, "high": 0.20}),
        "hospital medicine":  Distribution({"low": 0.20, "moderate": 0.40, "high": 0.40}),
        "emergency medicine": Distribution({"low": 0.05, "moderate": 0.25, "high": 0.70}),
        "specialty clinic":   Distribution({"low": 0.40, "moderate": 0.45, "high": 0.15}),
    }),
    verbosity_by_time_pressure=ConditionalDistribution({
        "low":      Distribution({"terse": 0.10, "moderate": 0.40, "thorough": 0.50}),
        "moderate": Distribution({"terse": 0.25, "moderate": 0.55, "thorough": 0.20}),
        "high":     Distribution({"terse": 0.60, "moderate": 0.35, "thorough": 0.05}),
    }),
    empathy=Distribution({
        "low":      0.20,
        "moderate": 0.45,
        "high":     0.35,
    }),
    comprehension_check_by_empathy=ConditionalDistribution({
        "low":      Distribution({"rarely": 0.60, "sometimes": 0.35, "always": 0.05}),
        "moderate": Distribution({"rarely": 0.20, "sometimes": 0.55, "always": 0.25}),
        "high":     Distribution({"rarely": 0.05, "sometimes": 0.35, "always": 0.60}),
    }),
)
