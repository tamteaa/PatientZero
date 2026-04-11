"""
Coverage analysis for an experiment.

Cell = joint of (patient literacy, anxiety, age_bucket, doctor empathy, verbosity).

**Target distribution**
- ``independence`` — product of one-dimensional marginals (legacy; ignores causal coupling).
- ``monte_carlo`` (default) — empirical frequencies from ``mc_samples`` draws through the real
  profile generators (matches the joint the simulator actually samples).

Coverage % = sum of target mass on cells hit at least once by completed simulations.

``distribution_match`` = ``1 - TVD`` between the Monte Carlo target and the empirical cell
distribution of counted simulations (diagnostic; ``None`` if nothing to compare).
"""

import json
import math
import random
from collections import Counter
from dataclasses import dataclass
from itertools import product
from typing import Literal

from core.config.doctor_distribution import US_BASELINE_DOCTOR
from core.config.patient_distribution import AGE_BUCKET_RANGES, US_ADULT_BASELINE
from core.generators.profile import StaticDoctorGenerator, StaticPatientGenerator
from core.types import (
    AgentProfile,
    Distribution,
    DoctorDistribution,
    PatientDistribution,
    SimulationRecord,
)

COVERAGE_PROBABILITY_FLOOR = 0.01
DEFAULT_MC_SAMPLES = 100_000

Cell = tuple[str, str, str, str, str]  # (literacy, anxiety, age_bucket, empathy, verbosity)


@dataclass(frozen=True)
class CoverageReport:
    cells_total: int
    cells_hit: int
    simulations_counted: int
    coverage_pct: float
    estimated_total_needed: int
    target_method: Literal["monte_carlo", "independence"] = "monte_carlo"
    mc_samples: int | None = None
    distribution_match: float | None = None

    def to_dict(self) -> dict:
        return {
            "cells_total": self.cells_total,
            "cells_hit": self.cells_hit,
            "simulations_counted": self.simulations_counted,
            "coverage_pct": self.coverage_pct,
            "estimated_total_needed": self.estimated_total_needed,
            "target_method": self.target_method,
            "mc_samples": self.mc_samples,
            "distribution_match": self.distribution_match,
        }


# ── Marginalization (independence target) ─────────────────────────────────────

def _chain(parent: Distribution, cond) -> Distribution:
    out: dict[str, float] = {}
    for parent_val, p_parent in parent.weights.items():
        child_dist = cond.by_parent[parent_val]
        for child_val, p_child in child_dist.weights.items():
            out[child_val] = out.get(child_val, 0.0) + p_parent * p_child
    return Distribution(out)


def patient_marginals(dist: PatientDistribution):
    education_marginal = _chain(dist.age, dist.education_by_age)
    literacy_marginal = _chain(education_marginal, dist.literacy_by_education)
    anxiety_marginal = _chain(dist.age, dist.anxiety_by_age)
    return literacy_marginal, anxiety_marginal, dist.age


def doctor_marginals(dist: DoctorDistribution):
    time_pressure_marginal = _chain(dist.setting, dist.time_pressure_by_setting)
    verbosity_marginal = _chain(time_pressure_marginal, dist.verbosity_by_time_pressure)
    return dist.empathy, verbosity_marginal


def build_cell_targets_independence(
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


def build_cell_targets_monte_carlo(
    patient_dist: PatientDistribution,
    doctor_dist: DoctorDistribution,
    n_samples: int,
    rng: random.Random | None = None,
) -> dict[Cell, float]:
    r = rng or random.Random()
    counts: Counter[Cell] = Counter()
    for _ in range(n_samples):
        p = StaticPatientGenerator(distribution=patient_dist).generate(1, rng=r)[0]
        d = StaticDoctorGenerator(distribution=doctor_dist).generate(1, rng=r)[0]
        cell = _profiles_to_cell(p, d)
        if cell:
            counts[cell] += 1
    total = sum(counts.values())
    if total == 0:
        return {}
    return {c: counts[c] / total for c in counts}


def bucket_age(age: int) -> str | None:
    for label, (lo, hi) in AGE_BUCKET_RANGES.items():
        if lo <= age <= hi:
            return label
    return None


def _profiles_to_cell(patient: AgentProfile, doctor: AgentProfile) -> Cell | None:
    try:
        pt = patient.traits
        dt = doctor.traits
        age = int(pt["age"])
        age_bucket = bucket_age(age)
        if age_bucket is None:
            return None
        return (
            pt["literacy"],
            pt["anxiety"],
            age_bucket,
            dt["empathy"],
            dt["verbosity"],
        )
    except (KeyError, ValueError, TypeError):
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


def _tvd(p: dict[Cell, float], q: dict[Cell, float]) -> float:
    keys = set(p) | set(q)
    return 0.5 * sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in keys)


def _empirical_from_sims(sims: list[SimulationRecord], cell_keys: set[Cell]) -> dict[Cell, float]:
    observed: list[Cell] = []
    for sim in sims:
        c = _sim_to_cell(sim)
        if c and c in cell_keys:
            observed.append(c)
    if not observed:
        return {}
    cnt = Counter(observed)
    n = len(observed)
    return {cell: cnt[cell] / n for cell in cnt}


def compute_coverage(
    sims: list[SimulationRecord],
    patient_dist: PatientDistribution = US_ADULT_BASELINE,
    doctor_dist: DoctorDistribution = US_BASELINE_DOCTOR,
    *,
    target_method: Literal["monte_carlo", "independence"] = "monte_carlo",
    mc_samples: int = DEFAULT_MC_SAMPLES,
    mc_rng: random.Random | None = None,
) -> CoverageReport:
    if target_method == "independence":
        cell_targets = build_cell_targets_independence(patient_dist, doctor_dist)
        mc_n = None
    else:
        cell_targets = build_cell_targets_monte_carlo(
            patient_dist, doctor_dist, mc_samples, rng=mc_rng
        )
        mc_n = mc_samples

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
        nonzero = [p for p in cell_targets.values() if p > 0]
        estimated_needed = math.ceil(1.0 / min(nonzero)) if nonzero else 0

    cell_keys = set(cell_targets.keys())
    dist_match: float | None = None
    if cell_targets and counted > 0:
        q = _empirical_from_sims(sims, cell_keys)
        if q:
            dist_match = round(1.0 - _tvd(cell_targets, q), 4)

    return CoverageReport(
        cells_total=len(cell_targets),
        cells_hit=len(hit_cells),
        simulations_counted=counted,
        coverage_pct=coverage_pct,
        estimated_total_needed=estimated_needed,
        target_method=target_method,
        mc_samples=mc_n,
        distribution_match=dist_match,
    )
