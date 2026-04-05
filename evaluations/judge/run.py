"""
Run the JudgeAgent against hardcoded conversations and print scores.

Usage:
    uv run python -m evaluations.judge.run [--model MODEL]
"""

import argparse
import asyncio
import importlib
import pkgutil
import sys

from core.agents.judge import JudgeAgent
from core.llm.factory import parse_provider_model
from core.types import Transcript
import evaluations.judge as judge_pkg


def discover_cases() -> list[dict]:
    """Find all case modules in evaluations/judge/ that export TRANSCRIPT."""
    cases = []
    for info in pkgutil.iter_modules(judge_pkg.__path__):
        if info.name in ("run", "__init__"):
            continue
        mod = importlib.import_module(f"evaluations.judge.{info.name}")
        if hasattr(mod, "TRANSCRIPT"):
            cases.append({
                "label": getattr(mod, "LABEL", info.name),
                "transcript": mod.TRANSCRIPT,
                "expected_range": getattr(mod, "EXPECTED_RANGE", (0, 100)),
            })
    return cases


def print_scores(result: dict):
    fields = [
        ("Comprehension", "comprehension_score"),
        ("Factual Recall", "factual_recall"),
        ("Applied Reasoning", "applied_reasoning"),
        ("Explanation Quality", "explanation_quality"),
        ("Interaction Quality", "interaction_quality"),
    ]
    for label, key in fields:
        val = result.get(key)
        score = f"{val}" if val is not None else "N/A"
        print(f"    {label:<24} {score}")

    gap = result.get("confidence_comprehension_gap")
    if gap:
        print(f"    {'Confidence Gap':<24} {gap}")

    justification = result.get("justification")
    if justification:
        print(f"    {'Justification':<24} {justification}")


async def async_main(model: str):
    provider, model_name = parse_provider_model(model)
    judge = JudgeAgent(provider, model_name)

    cases = discover_cases()
    if not cases:
        print("No evaluation cases found.")
        return 1

    passed = 0
    failed = 0

    for case in cases:
        label = case["label"]
        lo, hi = case["expected_range"]

        print(f"\n{'='*60}")
        print(f"  {label}")
        print(f"  expected_comprehension=[{lo}-{hi}]")
        print(f"{'='*60}")

        result = await judge.evaluate(case["transcript"])

        print()
        print_scores(result)

        score = result.get("comprehension_score")
        if score is not None and lo <= score <= hi:
            print(f"\n  \033[32mPASS\033[0m  comprehension {score} in [{lo}-{hi}]")
            passed += 1
        elif score is not None:
            print(f"\n  \033[31mFAIL\033[0m  comprehension {score} not in [{lo}-{hi}]")
            failed += 1
        else:
            print(f"\n  \033[33mSKIP\033[0m  comprehension score was None (parse failure?)")
            failed += 1

    print(f"\n{'='*60}")
    print(f"  Results: {passed}/{passed + failed} cases in expected range")
    print(f"{'='*60}\n")

    return 0 if failed == 0 else 1


def main():
    parser = argparse.ArgumentParser(description="Judge evaluation on hardcoded conversations")
    parser.add_argument("--model", default="mock:default", help="LLM model for the judge")
    args = parser.parse_args()
    sys.exit(asyncio.run(async_main(args.model)))


if __name__ == "__main__":
    main()
