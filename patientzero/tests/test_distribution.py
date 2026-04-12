"""Tests for the generic Distribution/Conditional DAG.

Includes translation tests that reproduce the existing PatientDistribution /
DoctorDistribution baselines in the new form and cross-check against the
original marginalization (`_chain` in core/analysis/coverage.py).
"""

import math
import random

import pytest

from patientzero.distribution import Conditional, Distribution, Marginal


# ══ Construction / validation ═══════════════════════════════════════════════


def test_empty_distribution_is_valid():
    d = Distribution()
    assert d.traits == ()
    assert d.topo_order == ()
    assert d.sample() == {}


def test_single_marginal_from_dict():
    d = Distribution(age={"young": 0.3, "old": 0.7})
    assert d.traits == ("age",)
    assert isinstance(d.node("age"), Marginal)
    assert d.support["age"] == ["young", "old"]


def test_explicit_marginal_node():
    d = Distribution(age=Marginal({"young": 0.3, "old": 0.7}))
    assert isinstance(d.node("age"), Marginal)


def test_weights_must_sum_to_one():
    with pytest.raises(ValueError, match="sum to 1.0"):
        Distribution(age={"young": 0.3, "old": 0.3})


def test_weights_cannot_be_negative():
    with pytest.raises(ValueError, match="negative"):
        Distribution(age={"young": -0.1, "old": 1.1})


def test_empty_weights_rejected():
    with pytest.raises(ValueError, match="non-empty"):
        Distribution(age={})


def test_non_identifier_trait_name_rejected():
    with pytest.raises(ValueError, match="identifier"):
        Distribution(**{"age-bucket": {"young": 1.0}})


def test_conditional_unknown_parent():
    with pytest.raises(ValueError, match="unknown parent"):
        Distribution(
            literacy=Conditional("age", {"young": {"low": 1.0}}),
        )


def test_conditional_self_loop():
    with pytest.raises(ValueError, match="depends on itself"):
        Distribution(
            age=Conditional("age", {"young": {"young": 1.0}}),
        )


def test_cycle_detection():
    with pytest.raises(ValueError, match="Cycle detected"):
        Distribution(
            a=Conditional("b", {"x": {"p": 1.0}}),
            b=Conditional("a", {"p": {"x": 1.0}}),
        )


def test_conditional_empty_table():
    with pytest.raises(ValueError, match="empty table"):
        Conditional("age", {})


def test_conditional_inner_weights_validated():
    with pytest.raises(ValueError, match="sum to 1.0"):
        Conditional("age", {"young": {"low": 0.3, "high": 0.3}})


# ══ Topo order ══════════════════════════════════════════════════════════════


def test_topo_patient_chain():
    d = _build_patient_distribution()
    order = d.topo_order
    # causal chain: age → education → literacy → tendency; age → anxiety
    assert order.index("age") < order.index("education")
    assert order.index("education") < order.index("literacy")
    assert order.index("literacy") < order.index("tendency")
    assert order.index("age") < order.index("anxiety")


def test_topo_doctor_chain():
    d = _build_doctor_distribution()
    order = d.topo_order
    assert order.index("setting") < order.index("time_pressure")
    assert order.index("time_pressure") < order.index("verbosity")
    assert order.index("empathy") < order.index("comprehension_check")


def test_topo_respects_declaration_order_among_independents():
    d = Distribution(
        empathy={"low": 0.3, "high": 0.7},
        setting={"primary": 0.5, "ed": 0.5},
    )
    assert d.topo_order == ("empathy", "setting")


def test_parents_of_trait():
    d = _build_patient_distribution()
    assert d.parents("age") == ()
    assert d.parents("education") == ("age",)
    assert d.parents("literacy") == ("education",)
    assert d.parents("anxiety") == ("age",)


# ══ Sampling ════════════════════════════════════════════════════════════════


def test_sample_returns_all_traits():
    d = _build_patient_distribution()
    profile = d.sample(random.Random(42))
    assert set(profile.keys()) == {"age", "education", "literacy", "anxiety", "tendency"}


def test_sample_values_are_in_support():
    d = _build_patient_distribution()
    rng = random.Random(42)
    for _ in range(100):
        profile = d.sample(rng)
        for trait, value in profile.items():
            assert value in d.support[trait], f"{trait}={value} not in {d.support[trait]}"


def test_sample_is_deterministic_with_seeded_rng():
    d = _build_patient_distribution()
    a = d.sample(random.Random(42))
    b = d.sample(random.Random(42))
    assert a == b


def test_constraint_pins_trait():
    d = _build_patient_distribution()
    rng = random.Random(42)
    for _ in range(20):
        profile = d.sample(rng, literacy="low")
        assert profile["literacy"] == "low"


def test_constraint_downstream_conditioned_on_pin():
    """Pinning literacy='low' should cause tendency to always come from the
    low-literacy sub-distribution."""
    d = _build_patient_distribution()
    rng = random.Random(42)
    low_tendencies = set()
    for _ in range(300):
        profile = d.sample(rng, literacy="low")
        low_tendencies.add(profile["tendency"])
    expected_low = {"agrees even when confused", "asks few questions", "defers to authority"}
    assert low_tendencies.issubset(expected_low)


def test_constraint_on_unknown_trait_raises():
    d = _build_patient_distribution()
    with pytest.raises(KeyError, match="unknown trait"):
        d.sample(constraint_nope="x")


def test_constraint_value_not_in_support_raises():
    d = _build_patient_distribution()
    with pytest.raises(ValueError, match="not in support"):
        d.sample(literacy="nonexistent")


def test_sample_empirical_matches_age_marginal():
    """P(age='young') from samples should converge to 0.28."""
    d = _build_patient_distribution()
    rng = random.Random(12345)
    counts = {"young": 0, "middle": 0, "older": 0, "senior": 0}
    n = 20_000
    for _ in range(n):
        profile = d.sample(rng)
        counts[profile["age"]] += 1
    assert math.isclose(counts["young"] / n, 0.28, abs_tol=0.02)
    assert math.isclose(counts["middle"] / n, 0.35, abs_tol=0.02)


# ══ Marginalization ═════════════════════════════════════════════════════════


def test_marginal_of_root_is_identity():
    d = _build_patient_distribution()
    m = d.marginal("age")
    expected = {"young": 0.28, "middle": 0.35, "older": 0.25, "senior": 0.12}
    assert m.weights == expected


def test_marginal_of_conditional_matches_chain():
    """Cross-check: marginal('literacy') should equal the two-level _chain
    computation that core/analysis/coverage.py performs on the existing
    PatientDistribution."""
    d = _build_patient_distribution()
    our_marginal = d.marginal("literacy").weights

    # Direct equivalent of `_chain(_chain(age, edu_by_age), lit_by_edu)`:
    age = {"young": 0.28, "middle": 0.35, "older": 0.25, "senior": 0.12}
    edu_by_age = _EDUCATION_BY_AGE
    lit_by_edu = _LITERACY_BY_EDUCATION

    edu_marginal: dict[str, float] = {}
    for a_val, a_p in age.items():
        for e_val, e_p in edu_by_age[a_val].items():
            edu_marginal[e_val] = edu_marginal.get(e_val, 0.0) + a_p * e_p

    lit_marginal: dict[str, float] = {}
    for e_val, e_p in edu_marginal.items():
        for l_val, l_p in lit_by_edu[e_val].items():
            lit_marginal[l_val] = lit_marginal.get(l_val, 0.0) + e_p * l_p

    for k, v in lit_marginal.items():
        assert math.isclose(our_marginal[k], v, abs_tol=1e-9), (
            f"marginal mismatch at {k}: {our_marginal[k]} vs {v}"
        )


def test_marginal_sums_to_one():
    d = _build_patient_distribution()
    for trait in d.traits:
        m = d.marginal(trait)
        total = sum(m.weights.values())
        assert math.isclose(total, 1.0, abs_tol=1e-9)


def test_marginal_unknown_trait_raises():
    d = _build_patient_distribution()
    with pytest.raises(KeyError):
        d.marginal("nonexistent")


# ══ Cell enumeration ════════════════════════════════════════════════════════


def test_full_joint_sums_to_one():
    d = _build_patient_distribution()
    cells = d.cells()
    total = sum(p for _, p in cells)
    assert math.isclose(total, 1.0, abs_tol=1e-9)


def test_cells_sorted_descending():
    d = _build_patient_distribution()
    cells = d.cells("age", "literacy")
    probs = [p for _, p in cells]
    assert probs == sorted(probs, reverse=True)


def test_subset_cells_sum_to_one():
    d = _build_patient_distribution()
    cells = d.cells("age", "literacy")
    total = sum(p for _, p in cells)
    assert math.isclose(total, 1.0, abs_tol=1e-9)


def test_subset_cells_marginalize_correctly():
    """cells('literacy') should match marginal('literacy')."""
    d = _build_patient_distribution()
    cells = dict(d.cells("literacy"))
    marginal = d.marginal("literacy").weights
    for (value,), p in cells.items():
        assert math.isclose(p, marginal[value], abs_tol=1e-9)


def test_unknown_trait_in_cells_raises():
    d = _build_patient_distribution()
    with pytest.raises(KeyError):
        list(d.cells("nonexistent"))


# ══ Reweight / replace ══════════════════════════════════════════════════════


def test_reweight_replaces_trait():
    d = _build_patient_distribution()
    d2 = d.reweight("age", {"young": 0.5, "middle": 0.5, "older": 0.0, "senior": 0.0})
    assert isinstance(d2.node("age"), Marginal)
    assert d2.node("age").weights["young"] == 0.5
    # Original unchanged
    assert d.node("age").weights["young"] == 0.28


def test_reweight_with_new_value_raises():
    d = _build_patient_distribution()
    with pytest.raises(ValueError, match="not handled by downstream conditional"):
        d.reweight("age", {"teen": 0.5, "adult": 0.5})


def test_reweight_sampling_respects_new_weights():
    d = _build_patient_distribution()
    d2 = d.reweight(
        "age", {"young": 1.0, "middle": 0.0, "older": 0.0, "senior": 0.0}
    )
    rng = random.Random(42)
    for _ in range(50):
        profile = d2.sample(rng)
        assert profile["age"] == "young"


def test_replace_with_conditional():
    d = _build_patient_distribution()
    new_lit = Conditional("education", {
        "less than high school": {"low": 1.0, "moderate": 0.0, "high": 0.0},
        "high school diploma":   {"low": 1.0, "moderate": 0.0, "high": 0.0},
        "some college":          {"low": 1.0, "moderate": 0.0, "high": 0.0},
        "bachelor's degree":     {"low": 1.0, "moderate": 0.0, "high": 0.0},
        "graduate degree":       {"low": 1.0, "moderate": 0.0, "high": 0.0},
    })
    d2 = d.replace("literacy", new_lit)
    rng = random.Random(42)
    for _ in range(50):
        profile = d2.sample(rng)
        assert profile["literacy"] == "low"


def test_reweight_unknown_trait_raises():
    d = _build_patient_distribution()
    with pytest.raises(KeyError):
        d.reweight("nonexistent", {"x": 1.0})


# ══ Fixtures ════════════════════════════════════════════════════════════════


_EDUCATION_BY_AGE = {
    "young": {
        "less than high school": 0.08,
        "high school diploma":   0.28,
        "some college":          0.30,
        "bachelor's degree":     0.24,
        "graduate degree":       0.10,
    },
    "middle": {
        "less than high school": 0.10,
        "high school diploma":   0.28,
        "some college":          0.26,
        "bachelor's degree":     0.24,
        "graduate degree":       0.12,
    },
    "older": {
        "less than high school": 0.14,
        "high school diploma":   0.32,
        "some college":          0.22,
        "bachelor's degree":     0.20,
        "graduate degree":       0.12,
    },
    "senior": {
        "less than high school": 0.22,
        "high school diploma":   0.38,
        "some college":          0.18,
        "bachelor's degree":     0.14,
        "graduate degree":       0.08,
    },
}

_LITERACY_BY_EDUCATION = {
    "less than high school": {"low": 0.75, "moderate": 0.22, "high": 0.03},
    "high school diploma":   {"low": 0.40, "moderate": 0.48, "high": 0.12},
    "some college":          {"low": 0.20, "moderate": 0.55, "high": 0.25},
    "bachelor's degree":     {"low": 0.08, "moderate": 0.42, "high": 0.50},
    "graduate degree":       {"low": 0.03, "moderate": 0.27, "high": 0.70},
}


def _build_patient_distribution() -> Distribution:
    """Generic reconstruction of US_ADULT_BASELINE from core/config/patient_distribution.py."""
    return Distribution(
        age={"young": 0.28, "middle": 0.35, "older": 0.25, "senior": 0.12},
        education=Conditional("age", _EDUCATION_BY_AGE),
        literacy=Conditional("education", _LITERACY_BY_EDUCATION),
        anxiety=Conditional("age", {
            "young":  {"low": 0.35, "moderate": 0.45, "high": 0.20},
            "middle": {"low": 0.30, "moderate": 0.42, "high": 0.28},
            "older":  {"low": 0.25, "moderate": 0.38, "high": 0.37},
            "senior": {"low": 0.20, "moderate": 0.35, "high": 0.45},
        }),
        tendency=Conditional("literacy", {
            "low": {
                "agrees even when confused": 0.50,
                "asks few questions":        0.30,
                "defers to authority":       0.20,
            },
            "moderate": {
                "asks clarifying questions":              0.40,
                "agrees mostly but pushes back sometimes": 0.35,
                "follows along but misses nuance":         0.25,
            },
            "high": {
                "asks direct targeted questions": 0.45,
                "challenges assumptions":         0.30,
                "wants data and specifics":       0.25,
            },
        }),
    )


def _build_doctor_distribution() -> Distribution:
    """Generic reconstruction of US_BASELINE_DOCTOR from core/config/doctor_distribution.py."""
    return Distribution(
        setting={
            "primary care":       0.45,
            "hospital medicine":  0.20,
            "emergency medicine": 0.15,
            "specialty clinic":   0.20,
        },
        time_pressure=Conditional("setting", {
            "primary care":       {"low": 0.30, "moderate": 0.50, "high": 0.20},
            "hospital medicine":  {"low": 0.20, "moderate": 0.40, "high": 0.40},
            "emergency medicine": {"low": 0.05, "moderate": 0.25, "high": 0.70},
            "specialty clinic":   {"low": 0.40, "moderate": 0.45, "high": 0.15},
        }),
        verbosity=Conditional("time_pressure", {
            "low":      {"terse": 0.10, "moderate": 0.40, "thorough": 0.50},
            "moderate": {"terse": 0.25, "moderate": 0.55, "thorough": 0.20},
            "high":     {"terse": 0.60, "moderate": 0.35, "thorough": 0.05},
        }),
        empathy={"low": 0.20, "moderate": 0.45, "high": 0.35},
        comprehension_check=Conditional("empathy", {
            "low":      {"rarely": 0.60, "sometimes": 0.35, "always": 0.05},
            "moderate": {"rarely": 0.20, "sometimes": 0.55, "always": 0.25},
            "high":     {"rarely": 0.05, "sometimes": 0.35, "always": 0.60},
        }),
    )
