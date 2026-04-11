"""Ensure persisted optimization prompts stay compatible with build_doctor_prompt / build_patient_prompt."""

from __future__ import annotations

import string


class PromptTemplateError(ValueError):
    """Raised when a saved template cannot be rendered with the simulation stack."""


_DOCTOR_KEYS = frozenset({"profile", "scenario", "style", "style_instructions"})
_PATIENT_KEYS = frozenset({"profile"})


def _format_field_names(template: str) -> set[str]:
    names: set[str] = set()
    for _, field_name, _, _ in string.Formatter().parse(template):
        if field_name is not None:
            # "0" or "name.attr" — we only support simple names
            base = field_name.split(".")[0].split("[")[0]
            if base:
                names.add(base)
    return names


def validate_optimization_prompts(prompts: dict[str, str]) -> None:
    """
    Doctor and patient templates must include the same .format() field names as _DOCTOR / _PATIENT
    so SimulationService can render them at run time.
    """
    doctor = prompts.get("doctor")
    if doctor is not None:
        _validate_role_template(doctor, _DOCTOR_KEYS, "doctor")

    patient = prompts.get("patient")
    if patient is not None:
        _validate_role_template(patient, _PATIENT_KEYS, "patient")


def _validate_role_template(template: str, required: frozenset[str], role: str) -> None:
    if not template.strip():
        raise PromptTemplateError(f"{role} prompt template is empty")

    fields = _format_field_names(template)
    missing = required - fields
    if missing:
        raise PromptTemplateError(
            f"{role} prompt template must contain format fields {sorted(required)}; "
            f"missing {sorted(missing)} (found {sorted(fields)})"
        )

    # Smoke-render: catches some brace/syntax issues
    dummy = {k: f"<{k}>" for k in required}
    try:
        template.format(**dummy)
    except (KeyError, ValueError) as e:
        raise PromptTemplateError(f"{role} prompt template failed format smoke test: {e}") from e
