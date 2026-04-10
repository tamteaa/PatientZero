"""
Coverage analysis for an experiment.

Defines a "cell" as a joint of observable patient and doctor traits:
    (literacy, anxiety, age_bucket, empathy, verbosity)

Target cell probability is the product of the *marginals* of these five traits
under the experiment's target distribution. (This treats them as independent —
a simplification of the true joint, which has correlations via the causal
chain in the generators. Good enough for a first-order coverage metric.)

Coverage %    = sum of target probabilities of cells hit ≥ 1 time.
Estimated N   = ceil(1 / min_reasonable_cell_probability), where "reasonable"
                means p ≥ COVERAGE_PROBABILITY_FLOOR. This answers
                "how many sims do we need for every non-rare cell to be
                expected to land at least once?"
"""

import json
import math
from dataclasses import dataclass
from itertools import product

from core.config.doctor_distribution import US_BASELINE_DOCTOR
from core.config.patient_distribution import AGE_BUCKET_RANGES, US_ADULT_BASELINE
from core.types import (
    ConditionalDistribution,
    Distribution,
    DoctorDistribution,
    PatientDistribution,
    SimulationRecord,
)

# Cells rarer than this floor are ignored when sizing the experiment.
COVERAGE_PROBABILITY_FLOOR = 0.01


@dataclass(frozen=True)
class CoverageReport:
    cells_total: int
    cells_hit: int
    simulations_counted: int
    coverage_pct: float               # 0.0–1.0, weighted by target probability
    estimated_total_needed: int

    def to_dict(self) -> dict:
        return {
            "cells_total": self.cells_total,
            "cells_hit": self.cells_hit,
            "simulations_counted": self.simulations_counted,
            "coverage_pct": self.coverage_pct,
            "estimated_total_needed": self.estimated_total_needed,
        }


# ── Marginalization helpers ──────────────────────────────────────────────────

def _chain(parent: Distribution, cond: ConditionalDistribution) -> Distribution:
    """Compute P(child) = sum_parent P(parent) * P(child | parent)."""
    out: dict[str, float] = {}
    for parent_val, p_parent in parent.weights.items():
        child_dist = cond.by_parent[parent_val]
        for child_val, p_child in child_dist.weights.items():
            out[child_val] = out.get(child_val, 0.0) + p_parent * p_child
    return Distribution(out)


def patient_marginals(dist: PatientDistribution) -> tuple[Distribution, Distribution, Distribution]:
    """Returns (literacy, anxiety, age_bucket) marginals."""
    education_marginal = _chain(dist.age, dist.education_by_age)
    literacy_marginal = _chain(education_marginal, dist.literacy_by_education)
    anxiety_marginal = _chain(dist.age, dist.anxiety_by_age)
    return literacy_marginal, anxiety_marginal, dist.age


def doctor_marginals(dist: DoctorDistribution) -> tuple[Distribution, Distribution]:
    """Returns (empathy, verbosity) marginals."""
    time_pressure_marginal = _chain(dist.setting, dist.time_pressure_by_setting)
    verbosity_marginal = _chain(time_pressure_marginal, dist.verbosity_by_time_pressure)
    return dist.empathy, verbosity_marginal


# ── Cell space ───────────────────────────────────────────────────────────────

Cell = tuple[str, str, str, str, str]  # (literacy, anxiety, age_bucket, empathy, verbosity)


def build_cell_targets(
    patient_dist: PatientDistribution = US_ADULT_BASELINE,
    doctor_dist: DoctorDistribution = US_BASELINE_DOCTOR,
) -> dict[Cell, float]:
    literacy, anxiety, age_bucket = patient_marginals(patient_dist)
    empathy, verbosity = doctor_marginals(doctor_dist)

    cells: dict[Cell, float] = {}
    for lit, anx, age, emp, verb in product(
        literacy.weights, anxiety.weights, age_bucket.weights, empathy.weights, verbosity.weights
    ):
        p = (
            literacy.weights[lit]
            * anxiety.weights[anx]
            * age_bucket.weights[age]
            * empathy.weights[emp]
            * verbosity.weights[verb]
        )
        cells[(lit, anx, age, emp, verb)] = p
    return cells


def bucket_age(age: int) -> str | None:
    for label, (lo, hi) in AGE_BUCKET_RANGES.items():
        if lo <= age <= hi:
            return label
    return None


def _sim_to_cell(sim: SimulationRecord) -> Cell | None:
    try:
        config = json.loads(sim.config_json)
        patient_traits = config["patient"]["traits"]
        doctor_traits = config["doctor"]["traits"]
        age = int(patient_traits["age"])
        age_bucket = bucket_age(age)
        if age_bucket is None:
            return None
        return (
            patient_traits["literacy"],
            patient_traits["anxiety"],
            age_bucket,
            doctor_traits["empathy"],
            doctor_traits["verbosity"],
        )
    except (KeyError, ValueError, TypeError, json.JSONDecodeError):
        return None


# ── Coverage computation ─────────────────────────────────────────────────────

def compute_coverage(
    sims: list[SimulationRecord],
    patient_dist: PatientDistribution = US_ADULT_BASELINE,
    doctor_dist: DoctorDistribution = US_BASELINE_DOCTOR,
) -> CoverageReport:
    cell_targets = build_cell_targets(patient_dist, doctor_dist)
    hit_cells: set[Cell] = set()
    counted = 0

    for sim in sims:
        cell = _sim_to_cell(sim)
        if cell is None or cell not in cell_targets:
            continue
        hit_cells.add(cell)
        counted += 1

    coverage_pct = sum(cell_targets[c] for c in hit_cells)

    reasonable_cells = [p for p in cell_targets.values() if p >= COVERAGE_PROBABILITY_FLOOR]
    if reasonable_cells:
        min_p = min(reasonable_cells)
        estimated_needed = math.ceil(1.0 / min_p)
    else:
        # Fallback: no cell above the floor, use smallest non-zero cell
        nonzero = [p for p in cell_targets.values() if p > 0]
        estimated_needed = math.ceil(1.0 / min(nonzero)) if nonzero else 0

    return CoverageReport(
        cells_total=len(cell_targets),
        cells_hit=len(hit_cells),
        simulations_counted=counted,
        coverage_pct=coverage_pct,
        estimated_total_needed=estimated_needed,
    )
