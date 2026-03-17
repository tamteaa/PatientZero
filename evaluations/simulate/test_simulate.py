"""
Evaluation for simulation pipeline.

Imports core directly — no running server needed.
Requires a real LLM API key configured in .env (or use mock).

Usage:
    uv run python -m evaluations.simulate.test_simulate
"""

import asyncio
import sys

from core.agents.explainer import ExplainerAgent
from core.agents.patient import PatientAgent
from core.llm.factory import parse_provider_model
from core.simulation import Simulation
from core.types import AgentTrace, Persona, Scenario

# ── Test data ────────────────────────────────────────────────────────────────

PERSONA = Persona(
    name="Maria Santos",
    age="62",
    education="High school diploma",
    literacy_level="low",
    anxiety="high",
    prior_knowledge="none",
    communication_style="passive",
    backstory=(
        "Retired cafeteria worker. Relies on her daughter to explain medical "
        "paperwork. Tends to nod along even when confused, worried about being a burden."
    ),
)

SCENARIO = Scenario(
    test_name="Complete Blood Count (CBC)",
    results="WBC: 11.2 (H), RBC: 4.1, Hemoglobin: 10.8 (L), Hematocrit: 33%, Platelets: 245",
    normal_range="WBC: 4.5-11.0, RBC: 4.0-5.5, Hemoglobin: 12.0-16.0, Hematocrit: 36-46%, Platelets: 150-400",
    significance="Elevated WBC may indicate infection or inflammation. Low hemoglobin suggests possible anemia.",
)

SCENARIO_KEYWORDS = ["blood", "wbc", "hemoglobin", "anemia", "white blood cell", "red blood cell"]

MODEL = "mock:default"


# ── Checks ───────────────────────────────────────────────────────────────────

class Results:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors: list[str] = []

    def check(self, name: str, condition: bool, detail: str = ""):
        if condition:
            self.passed += 1
            print(f"  \033[32mPASS\033[0m  {name}")
        else:
            self.failed += 1
            self.errors.append(name)
            msg = f"  \033[31mFAIL\033[0m  {name}"
            if detail:
                msg += f" — {detail}"
            print(msg)


def evaluate_trace(trace: AgentTrace, mode: str, results: Results):
    """Run all checks on a completed trace."""
    steps = trace.steps

    # Turn count
    if mode == "static":
        results.check("Turn count (static = 2)", len(steps) == 2, f"got {len(steps)}")
    else:
        results.check("Turn count (dialog 4-8)", 4 <= len(steps) <= 8, f"got {len(steps)}")

    # Roles alternate starting with explainer
    expected_types = ["ExplainerAgent", "PatientAgent"]
    roles_correct = all(
        step.agent_type == expected_types[i % 2] for i, step in enumerate(steps)
    )
    results.check("Roles alternate (explainer first)", roles_correct)

    # No empty turns
    empty_steps = [i for i, s in enumerate(steps) if len(s.output.strip()) < 20]
    results.check("No empty/trivial turns (>20 chars each)", len(empty_steps) == 0, f"steps {empty_steps} too short")

    # No errors
    error_steps = [i for i, s in enumerate(steps) if s.error is not None]
    results.check("No step errors", len(error_steps) == 0, f"steps {error_steps} had errors")

    # Explainer mentions scenario keywords
    explainer_text = " ".join(s.output.lower() for s in steps if s.agent_type == "ExplainerAgent")
    keyword_hits = [kw for kw in SCENARIO_KEYWORDS if kw in explainer_text]
    results.check(
        "Explainer mentions scenario keywords",
        len(keyword_hits) >= 2,
        f"found {keyword_hits}",
    )

    # Patient has actual content (not just "ok" or "I understand")
    patient_steps = [s for s in steps if s.agent_type == "PatientAgent"]
    if patient_steps:
        longest_patient = max(len(s.output) for s in patient_steps)
        results.check("Patient gives substantive response", longest_patient > 50, f"longest: {longest_patient} chars")

    # Timing
    results.check("Trace has timing", trace.duration_ms > 0, f"{trace.duration_ms:.0f}ms")

    # Print transcript preview
    print()
    for s in steps:
        label = "\033[34mExplainer\033[0m" if s.agent_type == "ExplainerAgent" else "\033[32mPatient\033[0m"
        preview = s.output[:150].replace("\n", " ")
        if len(s.output) > 150:
            preview += "..."
        print(f"    {label} ({s.duration_ms:.0f}ms): {preview}")
    print(f"    Total: {trace.duration_ms:.0f}ms")
    print()


# ── Main ─────────────────────────────────────────────────────────────────────

async def run_simulation(style: str, mode: str) -> AgentTrace | None:
    """Run a simulation using the Simulation orchestrator."""
    try:
        provider, model = parse_provider_model(MODEL)
    except Exception as e:
        print(f"  \033[31mERROR\033[0m  Failed to get provider: {e}")
        return None

    explainer = ExplainerAgent(provider, model, style, mode, SCENARIO)
    patient = PatientAgent(provider, model, PERSONA)

    sim = Simulation(explainer, patient, mode)
    return await sim.run()


async def async_main():
    results = Results()
    test_cases = [
        ("clinical", "static"),
        ("analogy", "dialog"),
    ]

    for style, mode in test_cases:
        label = f"{style} + {mode}"
        print(f"\n{'='*60}")
        print(f"  Running: {PERSONA.name} | {label} | CBC")
        print(f"{'='*60}\n")

        trace = await run_simulation(style, mode)
        if trace is None:
            results.failed += 1
            results.errors.append(f"{label}: simulation failed")
            continue

        results.check(f"[{label}] Simulation completed", True)
        evaluate_trace(trace, mode, results)

    # Summary
    total = results.passed + results.failed
    print(f"\n{'='*60}")
    print(f"  Results: {results.passed}/{total} checks passed")
    if results.errors:
        print(f"  Failed: {', '.join(results.errors)}")
    print(f"{'='*60}\n")

    sys.exit(0 if results.failed == 0 else 1)


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
