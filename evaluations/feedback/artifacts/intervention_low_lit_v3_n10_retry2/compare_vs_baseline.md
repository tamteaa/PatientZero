# Low-literacy A/B (n=10): baseline vs `v2_low_literacy_checks`

## Experiments

| Role | `experiment_id` | Policy |
|------|-----------------|--------|
| Baseline | `baseline_low_lit_v2_n10_restart` | `baseline` |
| Candidate | `intervention_low_lit_v3_n10_retry2` | `v2_low_literacy_checks` |

**Protocol:** `patient_literacy=low`, `max_turns=6`, `n_runs=10`, model/judge `kimi:kimi-k2.5`, style `clinical`. All 10 sims completed and judged on both arms.

## Protocol caveat

Baseline was run with **`--sim-timeout-s 180`**; this candidate run used **`300`** (and post-hoc runner fixes for cancelled simulations). Treat the comparison as **strong directional evidence**, not a perfectly matched lab experiment, unless you rerun baseline at 300s with a fresh `experiment_id`.

## Deltas (candidate − baseline)

Means and Cohen’s *d* are computed from each arm’s `analysis_experiment.csv` only.

| Metric | Baseline | Candidate | Δ | Cohen’s *d* |
|--------|----------|-----------|---|------------|
| Comprehension | 79.1 | 86.0 | **+6.9** | 0.81 |
| Factual recall | 68.4 | 77.5 | **+9.1** | 0.65 |
| Applied reasoning | 78.9 | 87.3 | **+8.4** | 1.12 |
| Explanation quality | 82.1 | 84.2 | **+2.1** | 0.23 |
| Interaction quality | 84.5 | 90.3 | **+5.8** | 0.97 |

**Confidence–comprehension gap rate** (non-empty gap field / n): **80% → 60%** (**−20 pp**).

## Interpretation (feedback loop)

This satisfies the feedback-loop **core loop** for the **low-literacy** slice: identify failure mode → prompt intervention → controlled re-run → measure change with effect-size-style summary.

Remaining plan-aligned work is **breadth**, not plumbing: mixed-cohort regression check, optional high-literacy contrast for “narrow the literacy gap,” and further iterations if new failure clusters appear.
