import pytest

from core.feedback.template_validation import PromptTemplateError, validate_optimization_prompts

_DOCTOR_MIN = """\
You are a doctor.

{profile}

## Scenario
{scenario}

## Explanation Style: {style}
{style_instructions}

## Instructions
Speak clearly."""

_PATIENT_MIN = """\
You are a patient.

{profile}

## Guidelines
Respond naturally."""


def test_valid_seed_like_prompts():
    validate_optimization_prompts({"doctor": _DOCTOR_MIN, "patient": _PATIENT_MIN})


def test_doctor_missing_placeholder():
    bad = _DOCTOR_MIN.replace("{style_instructions}", "fixed text")
    with pytest.raises(PromptTemplateError, match="missing"):
        validate_optimization_prompts({"doctor": bad, "patient": _PATIENT_MIN})


def test_patient_missing_profile():
    with pytest.raises(PromptTemplateError, match="missing"):
        validate_optimization_prompts({"doctor": _DOCTOR_MIN, "patient": "no profile field here"})


def test_empty_doctor():
    with pytest.raises(PromptTemplateError, match="empty"):
        validate_optimization_prompts({"doctor": "   ", "patient": _PATIENT_MIN})
