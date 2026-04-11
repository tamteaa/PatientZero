import random

from core.generators.base import ScenarioGenerator
from core.types import Scenario

# ── Distributions ────────────────────────────────────────────────────────────

_TESTS = [
    {
        "name": "Complete Blood Count (CBC)",
        "components": [
            {"name": "WBC", "unit": "K/uL", "low": 4.5, "high": 11.0},
            {"name": "RBC", "unit": "M/uL", "low": 4.0, "high": 5.5},
            {"name": "Hemoglobin", "unit": "g/dL", "low": 12.0, "high": 16.0},
            {"name": "Hematocrit", "unit": "%", "low": 36.0, "high": 46.0},
            {"name": "Platelets", "unit": "K/uL", "low": 150.0, "high": 400.0},
        ],
        "significances": {
            "WBC": {"high": "may indicate infection or inflammation", "low": "may indicate bone marrow issues or immune deficiency"},
            "Hemoglobin": {"high": "may indicate dehydration or polycythemia", "low": "suggests possible anemia"},
            "Platelets": {"high": "may indicate inflammation or bone marrow disorder", "low": "may increase bleeding risk"},
        },
    },
    {
        "name": "Basic Metabolic Panel (BMP)",
        "components": [
            {"name": "Glucose", "unit": "mg/dL", "low": 70.0, "high": 100.0},
            {"name": "BUN", "unit": "mg/dL", "low": 7.0, "high": 20.0},
            {"name": "Creatinine", "unit": "mg/dL", "low": 0.6, "high": 1.2},
            {"name": "Sodium", "unit": "mEq/L", "low": 136.0, "high": 145.0},
            {"name": "Potassium", "unit": "mEq/L", "low": 3.5, "high": 5.0},
            {"name": "Calcium", "unit": "mg/dL", "low": 8.5, "high": 10.5},
        ],
        "significances": {
            "Glucose": {"high": "may indicate diabetes or pre-diabetes", "low": "may indicate hypoglycemia"},
            "BUN": {"high": "may indicate kidney dysfunction or dehydration", "low": "may indicate liver disease"},
            "Creatinine": {"high": "may indicate impaired kidney function", "low": "generally not clinically significant"},
            "Potassium": {"high": "may cause cardiac arrhythmias", "low": "may cause muscle weakness and cramps"},
        },
    },
    {
        "name": "Lipid Panel",
        "components": [
            {"name": "Total Cholesterol", "unit": "mg/dL", "low": 0.0, "high": 200.0},
            {"name": "LDL", "unit": "mg/dL", "low": 0.0, "high": 100.0},
            {"name": "HDL", "unit": "mg/dL", "low": 40.0, "high": 60.0},
            {"name": "Triglycerides", "unit": "mg/dL", "low": 0.0, "high": 150.0},
        ],
        "significances": {
            "Total Cholesterol": {"high": "increases cardiovascular disease risk"},
            "LDL": {"high": "major risk factor for heart disease and stroke"},
            "HDL": {"low": "reduces cardiovascular protection"},
            "Triglycerides": {"high": "may increase risk of heart disease and pancreatitis"},
        },
    },
    {
        "name": "Thyroid Panel",
        "components": [
            {"name": "TSH", "unit": "mIU/L", "low": 0.4, "high": 4.0},
            {"name": "Free T4", "unit": "ng/dL", "low": 0.8, "high": 1.8},
            {"name": "Free T3", "unit": "pg/mL", "low": 2.3, "high": 4.2},
        ],
        "significances": {
            "TSH": {"high": "suggests hypothyroidism (underactive thyroid)", "low": "suggests hyperthyroidism (overactive thyroid)"},
            "Free T4": {"high": "may indicate hyperthyroidism", "low": "may indicate hypothyroidism"},
        },
    },
    {
        "name": "Hemoglobin A1c (HbA1c)",
        "components": [
            {"name": "HbA1c", "unit": "%", "low": 4.0, "high": 5.6},
        ],
        "significances": {
            "HbA1c": {"high": "indicates elevated average blood sugar; above 6.5% suggests diabetes, 5.7-6.4% suggests pre-diabetes"},
        },
    },
    {
        "name": "Liver Function Panel",
        "components": [
            {"name": "ALT", "unit": "U/L", "low": 7.0, "high": 56.0},
            {"name": "AST", "unit": "U/L", "low": 10.0, "high": 40.0},
            {"name": "Alkaline Phosphatase", "unit": "U/L", "low": 44.0, "high": 147.0},
            {"name": "Bilirubin", "unit": "mg/dL", "low": 0.1, "high": 1.2},
            {"name": "Albumin", "unit": "g/dL", "low": 3.5, "high": 5.5},
        ],
        "significances": {
            "ALT": {"high": "may indicate liver damage or hepatitis"},
            "AST": {"high": "may indicate liver, heart, or muscle damage"},
            "Bilirubin": {"high": "may indicate liver disease or bile duct obstruction"},
            "Albumin": {"low": "may indicate liver disease or malnutrition"},
        },
    },
]


def _generate_value(
    component: dict, abnormal: bool, rng: random.Random | None = None
) -> tuple[float, str]:
    """Generate a value for a component, optionally abnormal. Returns (value, flag)."""
    r = rng or random
    low, high = component["low"], component["high"]
    spread = high - low

    if not abnormal:
        val = r.uniform(low, high)
        return round(val, 1), ""

    if r.random() < 0.5 and low > 0:
        # Low abnormal
        val = r.uniform(max(0, low - spread * 0.4), low - 0.1)
        return round(val, 1), "L"
    else:
        # High abnormal
        val = r.uniform(high + 0.1, high + spread * 0.4)
        return round(val, 1), "H"


class StaticScenarioGenerator(ScenarioGenerator):
    """Generates scenarios by sampling from medical test distributions."""

    def __init__(self, abnormal_ratio: float = 0.3):
        self.abnormal_ratio = abnormal_ratio

    def generate(self, n: int = 1, rng: random.Random | None = None) -> list[Scenario]:
        return [self._generate_one(rng=rng) for _ in range(n)]

    def _generate_one(self, rng: random.Random | None = None) -> Scenario:
        r = rng or random
        test = r.choice(_TESTS)
        results = []
        normals = []
        findings = []

        for comp in test["components"]:
            is_abnormal = r.random() < self.abnormal_ratio
            val, flag = _generate_value(comp, is_abnormal, rng=r)
            flag_str = f" ({flag})" if flag else ""
            results.append(f"{comp['name']}: {val}{flag_str}")
            normals.append(f"{comp['name']}: {comp['low']}-{comp['high']} {comp['unit']}")

            if flag and comp["name"] in test.get("significances", {}):
                sig = test["significances"][comp["name"]]
                direction = "high" if flag == "H" else "low"
                if direction in sig:
                    findings.append(f"{flag_str.strip()} {comp['name']} {sig[direction]}")

        significance = ". ".join(findings) + "." if findings else "All values within normal range."

        description = (
            f"Medical Test: {test['name']}\n"
            f"Results: {', '.join(results)}\n"
            f"Normal Range: {', '.join(normals)}\n"
            f"Clinical Significance: {significance}"
        )

        name_parts = [test["name"]]
        if findings:
            name_parts.append(findings[0].split(")")[0].replace("(", "").strip() if ")" in findings[0] else "Abnormal")
        else:
            name_parts.append("Normal")

        return Scenario(name=" - ".join(name_parts), description=description)
