"""Canonical medical example ExperimentConfig.

Imported by the backend (as the seed experiment on first boot) and by
``core/examples/medical/run.py`` as the demo script's input.
"""

from patientzero.agent import Agent
from patientzero.examples.medical.distributions import US_ADULT_PATIENT, US_BASELINE_DOCTOR
from patientzero.examples.medical.prompts import (
    DOCTOR_TEMPLATE,
    JUDGE_INSTRUCTIONS,
    JUDGE_RUBRIC,
    PATIENT_TEMPLATE,
)
from patientzero.types import ExperimentConfig, JudgeConfig


MEDICAL_EXAMPLE_CONFIG = ExperimentConfig(
    name="medical-default",
    agents=(
        Agent("doctor", DOCTOR_TEMPLATE, US_BASELINE_DOCTOR),
        Agent("patient", PATIENT_TEMPLATE, US_ADULT_PATIENT),
    ),
    judge=JudgeConfig(
        rubric=JUDGE_RUBRIC,
        instructions=JUDGE_INSTRUCTIONS,
        model=None,
    ),
    model="claude:claude-haiku-4-5-20251001",
    max_turns=4,
    num_optimizations=1,
)
