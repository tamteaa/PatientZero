"""
Run the JudgeAgent against hardcoded conversations and print scores.

Usage:
    uv run python -m evaluations.judge.run [--model MODEL] [--force]
"""

import argparse
import asyncio
import importlib
import json
import pkgutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from core.agents.judge import JudgeAgent
from core.llm.factory import parse_provider_model
from core.types import JudgeResult
import evaluations.judge.cases as cases_pkg

SCORE_FIELDS = [
    ("Comprehension", "comprehension_score"),
    ("Factual Recall", "factual_recall"),
    ("Applied Reasoning", "applied_reasoning"),
    ("Explanation Quality", "explanation_quality"),
    ("Interaction Quality", "interaction_quality"),
]

OUTPUT_DIR = Path("evaluations/judge/output")


def discover_cases() -> list[dict]:
    """Find all case modules in evaluations/judge/cases/ that export TRANSCRIPT."""
    cases = []
    for info in pkgutil.iter_modules(cases_pkg.__path__):
        if info.name.startswith("_"):
            continue
        mod = importlib.import_module(f"evaluations.judge.cases.{info.name}")
        if hasattr(mod, "TRANSCRIPT"):
            cases.append({
                "name": info.name,
                "label": getattr(mod, "LABEL", info.name),
                "transcript": mod.TRANSCRIPT,
                "expected": getattr(mod, "EXPECTED", {}),
            })
    return cases


def load_cached(name: str, model: str) -> JudgeResult | None:
    path = OUTPUT_DIR / f"{name}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        if data.get("model") == model:
            payload = dict(data.get("result", {}))
            payload.setdefault("model", model)
            return JudgeResult.from_dict(payload)
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def save_result(name: str, model: str, result: JudgeResult) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{name}.json"
    path.write_text(json.dumps({
        "model": model,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "result": result.to_dict(),
    }, indent=2))


def print_scores(result: JudgeResult, expected: dict):
    for label, key in SCORE_FIELDS:
        val = getattr(result, key)
        score = f"{val}" if val is not None else "N/A"
        exp = expected.get(key)
        exp_str = f"  (expected {exp[0]}-{exp[1]})" if exp else ""
        print(f"    {label:<24} {score}{exp_str}")

    if result.confidence_comprehension_gap:
        print(f"    {'Confidence Gap':<24} {result.confidence_comprehension_gap}")

    if result.justification:
        print(f"    {'Justification':<24} {result.justification}")


def check_scores(result: JudgeResult, expected: dict) -> tuple[int, int]:
    """Check all score dimensions. Returns (passed, failed)."""
    passed = 0
    failed = 0
    for label, key in SCORE_FIELDS:
        if key not in expected:
            continue
        lo, hi = expected[key]
        val = getattr(result, key)
        if val is not None and lo <= val <= hi:
            passed += 1
        elif val is not None:
            print(f"    \033[31mFAIL\033[0m {label}: {val} not in [{lo}-{hi}]")
            failed += 1
        else:
            print(f"    \033[33mSKIP\033[0m {label}: score was None")
            failed += 1
    return passed, failed


async def async_main(model: str, force: bool, case_filter: list[str] | None = None):
    provider, model_name = parse_provider_model(model)
    judge = JudgeAgent(provider, model_name)

    cases = discover_cases()
    if case_filter:
        cases = [c for c in cases if c["name"] in case_filter]
    if not cases:
        print("No evaluation cases found.")
        return 1

    total_passed = 0
    total_failed = 0
    cases_passed = 0
    cases_failed = 0

    for case in cases:
        name = case["name"]
        label = case["label"]
        expected = case["expected"]

        print(f"\n{'='*60}")
        print(f"  {label}")
        print(f"{'='*60}")

        cached = None if force else load_cached(name, model)
        if cached:
            print(f"  (cached)")
            result = cached
        else:
            result = await judge.evaluate(case["transcript"])
            save_result(name, model, result)

        print()
        print_scores(result, expected)
        print()

        p, f = check_scores(result, expected)
        total_passed += p
        total_failed += f

        if f == 0:
            print(f"  \033[32mPASS\033[0m  all {p} dimensions in range")
            cases_passed += 1
        else:
            cases_failed += 1

    print(f"\n{'='*60}")
    print(f"  Cases: {cases_passed}/{cases_passed + cases_failed} fully passed")
    print(f"  Scores: {total_passed}/{total_passed + total_failed} dimensions in range")
    print(f"{'='*60}\n")

    return 0 if total_failed == 0 else 1


def main():
    parser = argparse.ArgumentParser(description="Judge evaluation on hardcoded conversations")
    parser.add_argument("--model", default="mock:default", help="LLM model for the judge")
    parser.add_argument("--force", action="store_true", help="Re-run all cases, ignoring cache")
    parser.add_argument("--case", nargs="+", help="Run only specific cases by name (e.g. cbc_good confidence_gap)")
    args = parser.parse_args()
    sys.exit(asyncio.run(async_main(args.model, args.force, args.case)))


if __name__ == "__main__":
    main()
