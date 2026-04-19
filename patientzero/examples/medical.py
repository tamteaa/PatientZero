"""Self-contained medical example: doctor-patient conversation about test results.

End-to-end demo — scenarios, causal patient/doctor distributions, prompts,
judge rubric, and a runner that does baseline → optimize → optimized → report.

Run with:
    uv run python -m patientzero.examples.medical

Reused as a configuration by ``rq1.py`` / ``rq2.py`` indirectly: those files
paste the same scenarios, distributions, and prompts and pin patient
literacy to the cohort they study.
"""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from patientzero import Agent, Conditional, Distribution, Experiment, ExperimentConfig, JudgeConfig
from patientzero.analysis.comparison import build_report, print_report, write_report
from patientzero.config.settings import DB_PATH
from patientzero.db.database import Database


# ── Scenarios ─────────────────────────────────────────────────────────────────

CBC_ANEMIA = (
    "Medical Test: Complete Blood Count (CBC)\n"
    "Results: WBC: 11.2 (H), RBC: 4.1, Hemoglobin: 10.8 (L), Hematocrit: 33%, Platelets: 245\n"
    "Normal Range: WBC: 4.5-11.0, RBC: 4.0-5.5, Hemoglobin: 12.0-16.0, Hematocrit: 36-46%, Platelets: 150-400\n"
    "Clinical Significance: Elevated WBC may indicate infection or inflammation. Low hemoglobin suggests possible anemia."
)

HBA1C_PREDIABETES = (
    "Medical Test: Hemoglobin A1c (HbA1c)\n"
    "Results: HbA1c: 6.1%\n"
    "Normal Range: Normal: below 5.7%, Pre-diabetes: 5.7-6.4%, Diabetes: 6.5% or higher\n"
    "Clinical Significance: An HbA1c of 6.1% indicates pre-diabetes. Blood sugar has been elevated over the past 2-3 months."
)

METFORMIN_RX = (
    "Medical Test: Metformin Prescription\n"
    "Starting dose: 500mg once daily with dinner. Increase to 500mg twice daily after 2 weeks if tolerated. Maximum dose: 2000mg/day.\n"
    "Common side effects: nausea, diarrhea. Seek care for severe stomach pain, muscle pain, difficulty breathing, or unusual fatigue."
)


# ── Patient distribution (causal DAG) ─────────────────────────────────────────
# age → education → literacy → tendency
# age → anxiety
# age → scenario

US_ADULT_PATIENT = Distribution(
    age={"young": 0.28, "middle": 0.35, "older": 0.25, "senior": 0.12},
    education=Conditional(
        "age",
        {
            "young":  {"less than high school": 0.08, "high school diploma": 0.28, "some college": 0.30, "bachelor's degree": 0.24, "graduate degree": 0.10},
            "middle": {"less than high school": 0.10, "high school diploma": 0.28, "some college": 0.26, "bachelor's degree": 0.24, "graduate degree": 0.12},
            "older":  {"less than high school": 0.14, "high school diploma": 0.32, "some college": 0.22, "bachelor's degree": 0.20, "graduate degree": 0.12},
            "senior": {"less than high school": 0.22, "high school diploma": 0.38, "some college": 0.18, "bachelor's degree": 0.14, "graduate degree": 0.08},
        },
    ),
    literacy=Conditional(
        "education",
        {
            "less than high school": {"low": 0.75, "moderate": 0.22, "high": 0.03},
            "high school diploma":   {"low": 0.40, "moderate": 0.48, "high": 0.12},
            "some college":          {"low": 0.20, "moderate": 0.55, "high": 0.25},
            "bachelor's degree":     {"low": 0.08, "moderate": 0.42, "high": 0.50},
            "graduate degree":       {"low": 0.03, "moderate": 0.27, "high": 0.70},
        },
    ),
    anxiety=Conditional(
        "age",
        {
            "young":  {"low": 0.35, "moderate": 0.45, "high": 0.20},
            "middle": {"low": 0.30, "moderate": 0.42, "high": 0.28},
            "older":  {"low": 0.25, "moderate": 0.38, "high": 0.37},
            "senior": {"low": 0.20, "moderate": 0.35, "high": 0.45},
        },
    ),
    tendency=Conditional(
        "literacy",
        {
            "low":      {"agrees even when confused": 0.50, "asks few questions": 0.30, "defers to authority": 0.20},
            "moderate": {"asks clarifying questions": 0.40, "agrees mostly but pushes back sometimes": 0.35, "follows along but misses nuance": 0.25},
            "high":     {"asks direct targeted questions": 0.45, "challenges assumptions": 0.30, "wants data and specifics": 0.25},
        },
    ),
    scenario=Conditional(
        "age",
        {
            "young":  {CBC_ANEMIA: 0.55, HBA1C_PREDIABETES: 0.30, METFORMIN_RX: 0.15},
            "middle": {CBC_ANEMIA: 0.35, HBA1C_PREDIABETES: 0.40, METFORMIN_RX: 0.25},
            "older":  {CBC_ANEMIA: 0.25, HBA1C_PREDIABETES: 0.40, METFORMIN_RX: 0.35},
            "senior": {CBC_ANEMIA: 0.20, HBA1C_PREDIABETES: 0.35, METFORMIN_RX: 0.45},
        },
    ),
)


# ── Doctor distribution (causal DAG) ──────────────────────────────────────────
# setting → time_pressure → verbosity
# empathy → comprehension_checking

US_BASELINE_DOCTOR = Distribution(
    setting={"primary care": 0.45, "hospital medicine": 0.20, "emergency medicine": 0.15, "specialty clinic": 0.20},
    time_pressure=Conditional(
        "setting",
        {
            "primary care":       {"low": 0.30, "moderate": 0.50, "high": 0.20},
            "hospital medicine":  {"low": 0.20, "moderate": 0.40, "high": 0.40},
            "emergency medicine": {"low": 0.05, "moderate": 0.25, "high": 0.70},
            "specialty clinic":   {"low": 0.40, "moderate": 0.45, "high": 0.15},
        },
    ),
    verbosity=Conditional(
        "time_pressure",
        {
            "low":      {"terse": 0.10, "moderate": 0.40, "thorough": 0.50},
            "moderate": {"terse": 0.25, "moderate": 0.55, "thorough": 0.20},
            "high":     {"terse": 0.60, "moderate": 0.35, "thorough": 0.05},
        },
    ),
    empathy={"low": 0.20, "moderate": 0.45, "high": 0.35},
    comprehension_checking=Conditional(
        "empathy",
        {
            "low":      {"rarely": 0.60, "sometimes": 0.35, "always": 0.05},
            "moderate": {"rarely": 0.20, "sometimes": 0.55, "always": 0.25},
            "high":     {"rarely": 0.05, "sometimes": 0.35, "always": 0.60},
        },
    ),
)


# ── Prompts ───────────────────────────────────────────────────────────────────

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
    "comprehension_score":  "Overall patient understanding inferred from the transcript.",
    "factual_recall":       "Whether the patient retained key numbers, terms, and action items.",
    "applied_reasoning":    "Whether the patient could reason about next steps and implications.",
    "explanation_quality":  "Clarity, completeness, and medical accuracy of the doctor's explanation.",
    "interaction_quality":  "Responsiveness of the doctor: comprehension checks, adaptation, tone.",
}


# ── Experiment config ─────────────────────────────────────────────────────────

MEDICAL_EXAMPLE_CONFIG = ExperimentConfig(
    name="medical-default",
    agents=(
        Agent("doctor",  DOCTOR_TEMPLATE,  US_BASELINE_DOCTOR),
        Agent("patient", PATIENT_TEMPLATE, US_ADULT_PATIENT),
    ),
    judge=JudgeConfig(rubric=JUDGE_RUBRIC, instructions=JUDGE_INSTRUCTIONS, model=None),
    model="claude:claude-haiku-4-5-20251001",
    max_turns=3,
    seed=42,
    num_optimizations=1,
)


# ── Runner ────────────────────────────────────────────────────────────────────

SIMS_PER_ROUND = 2
RESULTS_PATH = Path(__file__).parent / "results_medical.json"


async def main() -> None:
    db = Database(DB_PATH)
    await db.init()
    try:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        config = replace(MEDICAL_EXAMPLE_CONFIG, name=f"{MEDICAL_EXAMPLE_CONFIG.name}-{stamp}")
        exp = await Experiment.create(config, db=db)

        print(f"experiment: {exp.id}  name: {config.name}")

        print(f"\n── baseline: {SIMS_PER_ROUND} sims ──")
        await exp.run(n=SIMS_PER_ROUND, concurrency=1)

        for round_idx in range(config.num_optimizations):
            print(f"\n── optimize #{round_idx + 1} ──")
            result = await exp.optimize()
            print(f"  new target: {result.new_target.id[:8]}")
            print(f"\n── optimized: {SIMS_PER_ROUND} sims ──")
            await exp.run(n=SIMS_PER_ROUND, concurrency=1)

        report = await build_report(exp)
        print_report(report)
        write_report(report, RESULTS_PATH)
        print(f"\nwrote {RESULTS_PATH}")
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
