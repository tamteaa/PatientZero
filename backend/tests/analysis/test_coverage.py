import json
import random

from core.analysis.coverage import build_cell_targets_monte_carlo, compute_coverage
from core.config.doctor_distribution import US_BASELINE_DOCTOR
from core.config.patient_distribution import AGE_BUCKET_RANGES, US_ADULT_BASELINE
from core.types import SimulationRecord


def test_monte_carlo_targets_sum_to_one():
    r = random.Random(42)
    cells = build_cell_targets_monte_carlo(
        US_ADULT_BASELINE, US_BASELINE_DOCTOR, n_samples=8_000, rng=r
    )
    total = sum(cells.values())
    assert 0.99 < total <= 1.0


def test_compute_coverage_monte_carlo_deterministic():
    r = random.Random(99)
    a = compute_coverage(
        [],
        US_ADULT_BASELINE,
        US_BASELINE_DOCTOR,
        target_method="monte_carlo",
        mc_samples=3_000,
        mc_rng=r,
    )
    r2 = random.Random(99)
    b = compute_coverage(
        [],
        US_ADULT_BASELINE,
        US_BASELINE_DOCTOR,
        target_method="monte_carlo",
        mc_samples=3_000,
        mc_rng=r2,
    )
    assert a.cells_total == b.cells_total
    assert abs(a.coverage_pct - b.coverage_pct) < 1e-9


def test_compute_coverage_independence_has_full_grid():
    rep = compute_coverage(
        [],
        US_ADULT_BASELINE,
        US_BASELINE_DOCTOR,
        target_method="independence",
    )
    assert rep.cells_total == 324
    assert rep.mc_samples is None
    assert rep.target_method == "independence"


def test_distribution_match_with_synthetic_sims():
    r = random.Random(7)
    targets = build_cell_targets_monte_carlo(
        US_ADULT_BASELINE, US_BASELINE_DOCTOR, n_samples=5_000, rng=r
    )
    assert targets
    lit, anx, age_bucket, emp, verb = next(iter(targets.keys()))
    lo, hi = AGE_BUCKET_RANGES[age_bucket]
    age = (lo + hi) // 2
    cfg = {
        "patient": {
            "traits": {
                "age": str(age),
                "literacy": lit,
                "anxiety": anx,
                "education": "high school diploma",
                "tendency": "asks direct targeted questions",
            }
        },
        "doctor": {
            "traits": {
                "empathy": emp,
                "verbosity": verb,
                "setting": "urban",
                "time_pressure": "low",
                "comprehension_checking": "moderate",
            }
        },
    }
    sim = SimulationRecord(
        id="s1",
        experiment_id="e1",
        persona_name="P",
        scenario_name="CBC",
        model="m",
        state="completed",
        config_json=json.dumps(cfg),
        duration_ms=1.0,
        created_at="",
        completed_at="",
    )

    rep = compute_coverage([sim], US_ADULT_BASELINE, US_BASELINE_DOCTOR, target_method="independence")
    assert rep.simulations_counted == 1
    assert rep.distribution_match is not None
