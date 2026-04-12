"""
Experiment analysis — aggregates judge scores across each agent's sampled traits.

The shape is derived from the experiment's actual distributions: group by
(agent_name, trait, value) and report per-metric mean/std/n per bucket.
No hardcoded dimension names — whatever traits the distributions declare
are what you get.
"""

import math

from fastapi import APIRouter, HTTPException

from backend.api.dependencies import repos

router = APIRouter()


# ── Stats helpers ─────────────────────────────────────────────────────────────


def _mean(vals: list[float]) -> float | None:
    return sum(vals) / len(vals) if vals else None


def _std(vals: list[float]) -> float | None:
    if len(vals) < 2:
        return None
    m = _mean(vals)
    assert m is not None
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))


def _score_stats(per_dim_values: dict[str, list[float]]) -> dict:
    out: dict[str, dict] = {}
    for dim, vals in per_dim_values.items():
        m = _mean(vals)
        s = _std(vals)
        out[dim] = {
            "mean": round(m, 2) if m is not None else None,
            "std": round(s, 2) if s is not None else None,
            "n": len(vals),
        }
    return out


def _row_dims(row: dict, dims: set[str]) -> dict[str, list[float]]:
    return {dim: [row[dim]] if row.get(dim) is not None else [] for dim in dims}


# ── Row building ──────────────────────────────────────────────────────────────


def _build_rows(experiment_id: str) -> tuple[list[dict], set[str]]:
    """Join completed simulations with their evaluations and flatten per-dim scores.

    Each returned row has: ``profiles`` (dict[agent → trait dict]) plus every
    judge rubric dimension at the top level as a single float (mean across
    judge_results for that dimension on that evaluation).
    Returns ``(rows, judge_dimensions)``.
    """
    pairs = repos.evaluations.list_completed_with_evaluations_for_experiment(experiment_id)
    rows: list[dict] = []
    dims: set[str] = set()
    for sim, ev in pairs:
        row: dict = {"profiles": sim.config.profiles}
        for judge in ev.judge_results:
            for name, value in judge.scores.items():
                dims.add(name)
        for dim in dims:
            vals = [
                j.scores.get(dim)
                for j in ev.judge_results
                if j.scores.get(dim) is not None
            ]
            row[dim] = (sum(vals) / len(vals)) if vals else None
        rows.append(row)
    return rows, dims


# ── Grouping ──────────────────────────────────────────────────────────────────


def _aggregate_per_dim(rows: list[dict], dims: set[str]) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {dim: [] for dim in dims}
    for row in rows:
        for dim in dims:
            v = row.get(dim)
            if v is not None:
                out[dim].append(v)
    return out


def _group_by_trait(
    rows: list[dict], dims: set[str], agent_name: str, trait: str
) -> dict[str, dict]:
    buckets: dict[str, list[dict]] = {}
    for row in rows:
        value = row.get("profiles", {}).get(agent_name, {}).get(trait)
        if value is None:
            continue
        buckets.setdefault(value, []).append(row)
    return {
        value: _score_stats(_aggregate_per_dim(bucket_rows, dims))
        for value, bucket_rows in buckets.items()
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/experiments/{exp_id}/analysis")
def get_experiment_analysis(exp_id: str):
    experiment = repos.experiments.get(exp_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")

    rows, dims = _build_rows(exp_id)
    if not rows:
        return {
            "total_evaluations": 0,
            "overall": {},
            "by_trait": {},
        }

    overall = _score_stats(_aggregate_per_dim(rows, dims))

    by_trait: dict[str, dict[str, dict]] = {}
    for agent in experiment.config.agents:
        for trait in agent.distribution.topo_order:
            key = f"{agent.name}.{trait}"
            by_trait[key] = _group_by_trait(rows, dims, agent.name, trait)

    return {
        "total_evaluations": len(rows),
        "overall": overall,
        "by_trait": by_trait,
    }
