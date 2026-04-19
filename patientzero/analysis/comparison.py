"""Paper-table reporter shared by the RQ example runners.

After an experiment completes its baseline + optimized rounds, build a
per-dimension comparison (baseline mean, optimized mean, Δ, Cohen's d with
pooled SD) and render it to stdout and a JSON artifact.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import mean, variance

from patientzero.experiment import Experiment


def _cohens_d(baseline: list[float], optimized: list[float]) -> float | None:
    if len(baseline) < 2 or len(optimized) < 2:
        return None
    n_a, n_b = len(baseline), len(optimized)
    pooled_var = ((n_a - 1) * variance(baseline) + (n_b - 1) * variance(optimized)) / (n_a + n_b - 2)
    if pooled_var <= 0.0:
        return None
    return (mean(optimized) - mean(baseline)) / math.sqrt(pooled_var)


async def _scores_by_target(
    experiment: Experiment,
) -> dict[str, dict[str, list[float]]]:
    sims = await experiment.simulations()
    sim_target = {sim.id: sim.config.optimization_target_id for sim in sims}
    evals = await experiment._repos.evaluations.list_for_experiment(experiment.id)

    out: dict[str, dict[str, list[float]]] = {}
    for ev in evals:
        target_id = sim_target.get(ev.simulation_id)
        if target_id is None:
            continue
        bucket = out.setdefault(target_id, {})
        for judge_result in ev.judge_results:
            for dim, value in judge_result.scores.items():
                if value is None:
                    continue
                bucket.setdefault(dim, []).append(float(value))
    return out


async def build_report(experiment: Experiment) -> dict:
    history = await experiment.history()
    chronological = list(reversed(history))
    if len(chronological) < 2:
        raise RuntimeError(
            f"Need ≥2 optimization targets to report baseline vs optimized; "
            f"have {len(chronological)}. Did the optimization round run?"
        )
    baseline_target = chronological[0]
    optimized_target = chronological[-1]

    scores = await _scores_by_target(experiment)
    baseline = scores.get(baseline_target.id, {})
    optimized = scores.get(optimized_target.id, {})
    dimensions = sorted(set(baseline) | set(optimized))

    rows = []
    for dim in dimensions:
        b = baseline.get(dim, [])
        o = optimized.get(dim, [])
        b_mean = mean(b) if b else None
        o_mean = mean(o) if o else None
        delta = (o_mean - b_mean) if (b_mean is not None and o_mean is not None) else None
        rows.append({
            "dimension": dim,
            "baseline_mean": b_mean,
            "optimized_mean": o_mean,
            "delta": delta,
            "cohens_d": _cohens_d(b, o),
            "n_baseline": len(b),
            "n_optimized": len(o),
        })

    return {
        "experiment": experiment.config.name,
        "experiment_id": experiment.id,
        "model": experiment.config.model,
        "max_turns": experiment.config.max_turns,
        "seed": experiment.config.seed,
        "baseline_target_id": baseline_target.id,
        "optimized_target_id": optimized_target.id,
        "rows": rows,
    }


def print_report(report: dict) -> None:
    print()
    print(f"── results: {report['experiment']} ──")
    print(f"  model={report['model']}  max_turns={report['max_turns']}  seed={report['seed']}")
    header = f"  {'dimension':<22} {'baseline':>9} {'optimized':>10} {'Δ':>7} {'d':>7} {'n':>7}"
    print(header)
    print("  " + "─" * (len(header) - 2))
    for row in report["rows"]:
        b = "n/a" if row["baseline_mean"] is None else f"{row['baseline_mean']:.2f}"
        o = "n/a" if row["optimized_mean"] is None else f"{row['optimized_mean']:.2f}"
        d = "n/a" if row["delta"] is None else f"{row['delta']:+.2f}"
        c = "n/a" if row["cohens_d"] is None else f"{row['cohens_d']:.2f}"
        n = f"{row['n_baseline']}/{row['n_optimized']}"
        print(f"  {row['dimension']:<22} {b:>9} {o:>10} {d:>7} {c:>7} {n:>7}")


def write_report(report: dict, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n")
