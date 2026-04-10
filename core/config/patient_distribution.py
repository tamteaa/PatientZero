"""
Default patient target distribution — the "US adult baseline."

Weights calibrated to:
- Age: US Census adult age pyramid (18+)
- Education | age: Census ACS educational attainment
- Literacy | education: NAAL 2003 health literacy
- Anxiety | age: NHIS health worry data
- Tendency | literacy: health psychology (agreement bias, assertiveness)
"""

from core.types import ConditionalDistribution, Distribution, PatientDistribution

# Label → (lo, hi) inclusive. Labels must match the age Distribution's keys below.
AGE_BUCKET_RANGES: dict[str, tuple[int, int]] = {
    "young":  (18, 35),
    "middle": (36, 55),
    "older":  (56, 75),
    "senior": (76, 89),
}


US_ADULT_BASELINE = PatientDistribution(
    age=Distribution({
        "young":  0.28,
        "middle": 0.35,
        "older":  0.25,
        "senior": 0.12,
    }),
    education_by_age=ConditionalDistribution({
        "young": Distribution({
            "less than high school": 0.08,
            "high school diploma":   0.28,
            "some college":          0.30,
            "bachelor's degree":     0.24,
            "graduate degree":       0.10,
        }),
        "middle": Distribution({
            "less than high school": 0.10,
            "high school diploma":   0.28,
            "some college":          0.26,
            "bachelor's degree":     0.24,
            "graduate degree":       0.12,
        }),
        "older": Distribution({
            "less than high school": 0.14,
            "high school diploma":   0.32,
            "some college":          0.22,
            "bachelor's degree":     0.20,
            "graduate degree":       0.12,
        }),
        "senior": Distribution({
            "less than high school": 0.22,
            "high school diploma":   0.38,
            "some college":          0.18,
            "bachelor's degree":     0.14,
            "graduate degree":       0.08,
        }),
    }),
    literacy_by_education=ConditionalDistribution({
        "less than high school": Distribution({"low": 0.75, "moderate": 0.22, "high": 0.03}),
        "high school diploma":   Distribution({"low": 0.40, "moderate": 0.48, "high": 0.12}),
        "some college":          Distribution({"low": 0.20, "moderate": 0.55, "high": 0.25}),
        "bachelor's degree":     Distribution({"low": 0.08, "moderate": 0.42, "high": 0.50}),
        "graduate degree":       Distribution({"low": 0.03, "moderate": 0.27, "high": 0.70}),
    }),
    anxiety_by_age=ConditionalDistribution({
        "young":  Distribution({"low": 0.35, "moderate": 0.45, "high": 0.20}),
        "middle": Distribution({"low": 0.30, "moderate": 0.42, "high": 0.28}),
        "older":  Distribution({"low": 0.25, "moderate": 0.38, "high": 0.37}),
        "senior": Distribution({"low": 0.20, "moderate": 0.35, "high": 0.45}),
    }),
    tendency_by_literacy=ConditionalDistribution({
        "low": Distribution({
            "agrees even when confused": 0.50,
            "asks few questions":        0.30,
            "defers to authority":       0.20,
        }),
        "moderate": Distribution({
            "asks clarifying questions":              0.40,
            "agrees mostly but pushes back sometimes": 0.35,
            "follows along but misses nuance":         0.25,
        }),
        "high": Distribution({
            "asks direct targeted questions": 0.45,
            "challenges assumptions":         0.30,
            "wants data and specifics":       0.25,
        }),
    }),
)
