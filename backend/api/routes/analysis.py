"""
Analysis endpoint — aggregates evaluation scores across dimensions per plan.md §2:

Key questions answered:
  1. Which patient types are left behind? (literacy, anxiety, age breakdown)
  2. Which concepts consistently confuse? (scenario breakdown)
  3. Which doctor behaviors cause failures? (empathy, verbosity, comp-checking)
  4. Where are confidence-comprehension gaps? (gap analysis)
  5. Which combinations are worst? (patient × doctor × scenario)

Stats: mean, std, n per group + Cohen's d effect sizes for ordered traits.
"""

import json
import math

from fastapi import APIRouter
from fastapi.responses import Response

from backend.api.dependencies import db

router = APIRouter()

# ── Stats helpers ─────────────────────────────────────────────────────────────

METRICS = [
    "comprehension_score",
    "factual_recall",
    "applied_reasoning",
    "explanation_quality",
    "interaction_quality",
]


def _mean(vals: list[float]) -> float | None:
    return sum(vals) / len(vals) if vals else None


def _std(vals: list[float]) -> float | None:
    if len(vals) < 2:
        return None
    m = _mean(vals)
    assert m is not None
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))


def _cohens_d(a: list[float], b: list[float]) -> float | None:
    """Standardised mean difference (positive = a > b)."""
    if len(a) < 2 or len(b) < 2:
        return None
    ma, mb = _mean(a), _mean(b)
    assert ma is not None and mb is not None
    var_a = sum((x - ma) ** 2 for x in a) / (len(a) - 1)
    var_b = sum((x - mb) ** 2 for x in b) / (len(b) - 1)
    pooled = math.sqrt(((len(a) - 1) * var_a + (len(b) - 1) * var_b) / (len(a) + len(b) - 2))
    return round((ma - mb) / pooled, 2) if pooled else None


def _score_stats(rows: list[dict]) -> dict:
    result = {}
    for metric in METRICS:
        vals = [r[metric] for r in rows if r.get(metric) is not None]
        m = _mean(vals)
        s = _std(vals)
        result[metric] = {
            "mean": round(m, 2) if m is not None else None,
            "std": round(s, 2) if s is not None else None,
            "n": len(vals),
        }
    return result


def _group_by(rows: list[dict], key_fn) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for row in rows:
        k = key_fn(row)
        if k:
            groups.setdefault(k, []).append(row)
    return groups


def _age_bucket(age_str: str | None) -> str | None:
    if not age_str:
        return None
    try:
        age = int(age_str)
    except (ValueError, TypeError):
        return None
    if age <= 35:
        return "18–35"
    elif age <= 55:
        return "36–55"
    elif age <= 75:
        return "56–75"
    else:
        return "76+"


# ── Query ─────────────────────────────────────────────────────────────────────

def _fetch_rows() -> list[dict]:
    """Fetch evaluations joined with simulation config.

    Each row surfaces per-metric means across all JudgeResults on the evaluation,
    so downstream grouping/stats code can stay metric-key-driven.
    """
    raw = db.conn.execute(
        """
        SELECT
            e.judge_results_json,
            s.persona_name, s.scenario_name, s.config_json
        FROM evaluations e
        JOIN simulations s ON s.id = e.simulation_id
        WHERE s.state = 'completed'
        ORDER BY e.created_at DESC
        """
    ).fetchall()

    rows = []
    for r in raw:
        row = dict(r)
        judge_results = json.loads(row.pop("judge_results_json", "[]") or "[]")
        for metric in METRICS:
            vals = [j.get(metric) for j in judge_results if j.get(metric) is not None]
            row[metric] = sum(vals) / len(vals) if vals else None
        gaps = [j.get("confidence_comprehension_gap") for j in judge_results if j.get("confidence_comprehension_gap")]
        row["confidence_comprehension_gap"] = gaps[0] if gaps else None
        try:
            cfg = json.loads(row.pop("config_json", "{}"))
            patient = cfg.get("patient", {})
            doctor = cfg.get("doctor", {})
            pt = patient.get("traits", {})
            dt = doctor.get("traits", {})
            row["patient_literacy"]  = pt.get("literacy")
            row["patient_anxiety"]   = pt.get("anxiety")
            row["patient_tendency"]  = pt.get("tendency")
            row["patient_age"]       = pt.get("age")
            row["patient_education"] = pt.get("education")
            row["patient_age_bucket"] = _age_bucket(pt.get("age"))
            row["doctor_empathy"]    = dt.get("empathy")
            row["doctor_verbosity"]  = dt.get("verbosity")
            row["doctor_comp_check"] = dt.get("comprehension_checking")
            row["doctor_time_pressure"] = dt.get("time_pressure")
        except Exception:
            pass
        rows.append(row)
    return rows


# ── Effect sizes ──────────────────────────────────────────────────────────────

def _effect_sizes(groups: dict[str, list[dict]], metric: str) -> dict:
    """Cohen's d for key group comparisons on a given metric."""

    def vals(key: str) -> list[float]:
        return [r[metric] for r in groups.get(key, []) if r.get(metric) is not None]

    return {
        "high_vs_low": _cohens_d(vals("high"), vals("low")),
        "high_vs_moderate": _cohens_d(vals("high"), vals("moderate")),
        "moderate_vs_low": _cohens_d(vals("moderate"), vals("low")),
    }


def _verbosity_effect(groups: dict[str, list[dict]], metric: str) -> dict:
    def vals(key: str) -> list[float]:
        return [r[metric] for r in groups.get(key, []) if r.get(metric) is not None]

    return {
        "thorough_vs_terse": _cohens_d(vals("thorough"), vals("terse")),
        "thorough_vs_moderate": _cohens_d(vals("thorough"), vals("moderate")),
        "moderate_vs_terse": _cohens_d(vals("moderate"), vals("terse")),
    }


# ── Gap analysis ──────────────────────────────────────────────────────────────

def _gap_analysis(rows: list[dict]) -> dict:
    """Confidence-comprehension gap rates overall and by key dimensions."""
    total = len(rows)
    if total == 0:
        return {"total_with_gap": 0, "gap_rate": 0.0, "by_literacy": {}, "by_scenario": {}}

    def has_gap(r: dict) -> bool:
        v = r.get("confidence_comprehension_gap")
        return bool(v and str(v).strip().lower() not in ("null", "none", ""))

    with_gap = [r for r in rows if has_gap(r)]
    gap_rate = round(len(with_gap) / total * 100, 1)

    def _rate_by(key_fn) -> dict:
        groups = _group_by(rows, key_fn)
        result = {}
        for k, grp in groups.items():
            n_gap = sum(1 for r in grp if has_gap(r))
            result[k] = {"rate": round(n_gap / len(grp) * 100, 1), "n": len(grp), "n_gap": n_gap}
        return result

    return {
        "total_with_gap": len(with_gap),
        "gap_rate": gap_rate,
        "by_literacy": _rate_by(lambda r: r.get("patient_literacy")),
        "by_scenario": _rate_by(lambda r: r.get("scenario_name")),
        "by_doctor_empathy": _rate_by(lambda r: r.get("doctor_empathy")),
    }


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get("/analysis")
def get_analysis():
    rows = _fetch_rows()

    empty = {
        "total_evaluations": 0,
        "overall": {},
        "by_patient_literacy": {},
        "by_patient_anxiety": {},
        "by_patient_age": {},
        "by_doctor_empathy": {},
        "by_doctor_verbosity": {},
        "by_doctor_comprehension_checking": {},
        "by_scenario": {},
        "effect_sizes": {},
        "gap_analysis": {"total_with_gap": 0, "gap_rate": 0.0, "by_literacy": {}, "by_scenario": {}, "by_doctor_empathy": {}},
        "worst_combinations": [],
    }
    if not rows:
        return empty

    # ── Grouped stats ────────────────────────────────────────────────────────
    lit_groups  = _group_by(rows, lambda r: r.get("patient_literacy"))
    anx_groups  = _group_by(rows, lambda r: r.get("patient_anxiety"))
    age_groups  = _group_by(rows, lambda r: r.get("patient_age_bucket"))
    emp_groups  = _group_by(rows, lambda r: r.get("doctor_empathy"))
    verb_groups = _group_by(rows, lambda r: r.get("doctor_verbosity"))
    cc_groups   = _group_by(rows, lambda r: r.get("doctor_comp_check"))
    scen_groups = _group_by(rows, lambda r: r.get("scenario_name"))

    by_literacy   = {k: _score_stats(v) for k, v in lit_groups.items()}
    by_anxiety    = {k: _score_stats(v) for k, v in anx_groups.items()}
    by_age        = {k: _score_stats(v) for k, v in age_groups.items()}
    by_empathy    = {k: _score_stats(v) for k, v in emp_groups.items()}
    by_verbosity  = {k: _score_stats(v) for k, v in verb_groups.items()}
    by_comp_check = {k: _score_stats(v) for k, v in cc_groups.items()}
    by_scenario   = {k: _score_stats(v) for k, v in scen_groups.items()}

    # ── Effect sizes ─────────────────────────────────────────────────────────
    effect_sizes = {
        "literacy": {
            metric: _effect_sizes(lit_groups, metric) for metric in METRICS
        },
        "anxiety": {
            metric: _effect_sizes(anx_groups, metric) for metric in METRICS
        },
        "empathy": {
            metric: _effect_sizes(emp_groups, metric) for metric in METRICS
        },
        "verbosity": {
            metric: _verbosity_effect(verb_groups, metric) for metric in METRICS
        },
    }

    # ── Worst combinations ───────────────────────────────────────────────────
    # patient literacy × doctor empathy × doctor verbosity × scenario
    combos: dict[tuple, list[dict]] = {}
    for row in rows:
        lit  = row.get("patient_literacy")
        emp  = row.get("doctor_empathy")
        verb = row.get("doctor_verbosity")
        scen = row.get("scenario_name")
        if lit and emp and scen:
            combos.setdefault((lit, emp, verb or "?", scen), []).append(row)

    worst = []
    for (lit, emp, verb, scen), combo_rows in combos.items():
        cs_vals = [r["comprehension_score"] for r in combo_rows if r.get("comprehension_score") is not None]
        if not cs_vals:
            continue
        worst.append({
            "patient_literacy": lit,
            "doctor_empathy": emp,
            "doctor_verbosity": verb,
            "scenario": scen,
            "mean_comprehension": round(sum(cs_vals) / len(cs_vals), 1),
            "scores": _score_stats(combo_rows),
            "n": len(cs_vals),
        })

    worst.sort(key=lambda x: x["mean_comprehension"])

    return {
        "total_evaluations": len(rows),
        "overall": _score_stats(rows),
        "by_patient_literacy": by_literacy,
        "by_patient_anxiety": by_anxiety,
        "by_patient_age": by_age,
        "by_doctor_empathy": by_empathy,
        "by_doctor_verbosity": by_verbosity,
        "by_doctor_comprehension_checking": by_comp_check,
        "by_scenario": by_scenario,
        "effect_sizes": effect_sizes,
        "gap_analysis": _gap_analysis(rows),
        "worst_combinations": worst[:10],
    }


@router.get("/analysis/export.csv")
def export_csv():
    """Export raw evaluation rows with traits as CSV."""
    rows = _fetch_rows()
    if not rows:
        return Response(content="", media_type="text/csv")

    cols = [
        "persona_name", "scenario_name",
        "patient_literacy", "patient_anxiety", "patient_tendency",
        "patient_age", "patient_age_bucket", "patient_education",
        "doctor_empathy", "doctor_verbosity", "doctor_comp_check", "doctor_time_pressure",
        "comprehension_score", "factual_recall", "applied_reasoning",
        "explanation_quality", "interaction_quality", "confidence_comprehension_gap",
    ]

    lines = [",".join(cols)]
    for row in rows:
        values = []
        for col in cols:
            val = row.get(col)
            if val is None:
                values.append("")
            else:
                s = str(val).replace('"', '""')
                values.append(f'"{s}"' if ("," in s or '"' in s) else s)
        lines.append(",".join(values))

    return Response(
        content="\n".join(lines),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=patientzero_analysis.csv"},
    )
