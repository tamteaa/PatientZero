# Feedback loop — evidence-backed recommendations

This document closes the **manual feedback loop** for the **low–health-literacy** cohort, using in-repo batches and per-run CSVs (not whole-DB `analysis.json` from the runner). Product direction and DSPy work live in **`todos.md`**.

## What shipped in-repo

- **DB `experiments` + `optimization_targets`** — seeded prompts from `prompts.py`; **Optimize** stub + `FeedbackService` (`todos.md`).
- **Simulations** store **`experiments.id` (FK)**; optional **`batch_id`** in `config_json` for A/B labels. Compare API: prefer **`baseline_batch_id` / `candidate_batch_id`**; legacy **`baseline_experiment_id` / `candidate_experiment_id`** unchanged. **`simulations.optimization_target_id`** (and config mirror) supports **`by_optimization_target_id`** on **`GET /api/analysis`**.
- **Versioned doctor policies** in `core/agents/prompts.py`: `baseline`, `v2_low_literacy_checks`, `v3_anxiety_first` (overlays on top of the current optimization target template).
- **`SimulationService`** loads the experiment’s **current optimization target** templates when building agents.
- **Analysis slicing + compare API**: `GET /api/analysis/compare?...` (`backend/api/routes/analysis.py`); list/revert targets via `/api/experiments/{id}/optimization-targets` and `POST .../optimization-target/current`.
- **Batch runner**: `evaluations/feedback/run_feedback_cycle.py` — requires `--experiment-db-id` + `--batch-id` (or deprecated `--experiment-id`).
- **Runbook**: `evaluations/feedback/RUNBOOK.md`.

## Primary result — low-literacy A/B at n=10 (post-restart)

| Arm | Batch label (`batch_id` / legacy `config_json.experiment_id`) | Policy |
|-----|---------------------------------------------------------------|--------|
| Baseline | `baseline_low_lit_v2_n10_restart` | `baseline` |
| Intervention | `intervention_low_lit_v3_n10_retry2` | `v2_low_literacy_checks` |

**Protocol:** `patient_literacy=low`, `max_turns=6`, `n_runs=10`, `kimi:kimi-k2.5` for sim + judge, style `clinical`. **10/10 completed and judged** on both arms.

**Comparison artifact:** `evaluations/feedback/artifacts/intervention_low_lit_v3_n10_retry2/compare_vs_baseline.{json,md}`

**Summary (from `analysis_experiment.csv` on each arm):**

- Comprehension **+6.9** (79.1 → 86.0), Cohen’s *d* ≈ **0.81**
- Factual recall **+9.1**, *d* ≈ **0.65**
- Applied reasoning **+8.4**, *d* ≈ **1.12**
- Explanation quality **+2.1**, *d* ≈ **0.23**
- Interaction quality **+5.8**, *d* ≈ **0.97**
- Confidence–comprehension **gap rate 80% → 60%** (−20 pp)

**Caveat:** Baseline used **`--sim-timeout-s 180`**; intervention used **`300`**. For a perfectly matched protocol, rerun baseline with `300` and a new `experiment_id`, then re-compare.

**Decision:** **Keep `v2_low_literacy_checks` as the preferred policy for low-literacy cohorts** in this stack, subject to the timeout caveat and ongoing monitoring.

## Earlier iterations (context)

- **Mixed cohort (`baseline_v1` vs `intervention_v2`):** large deltas but **no low-literacy patients** in the intervention draw — invalid for the literacy hypothesis. See `evaluations/feedback/artifacts/intervention_v2/compare_vs_baseline.md`.
- **Pilot low-literacy (`baseline_low_lit_v1` vs `intervention_low_lit_v2`):** n=3 directional lift + gap improvement; superseded by n=10 evidence above.

## Not done yet (breadth validation, not plumbing)

1. **Mixed-cohort / non-target regression run** — same batch shape **without** forcing low literacy (or stratified), to check for major regressions outside the target cohort.
2. **Literacy contrast** — plan asks whether high- vs low-literacy **gaps narrow**; we have not yet run a paired high-literacy arm at the same N/protocol.
3. **Next hypothesis** — if analysis shows anxiety-driven failures, run `v3_anxiety_first` with `patient_anxiety=high` using the same runner pattern.
4. **Scale** — optional n=20–40 rerun for stability; same compare pattern.

## Operational guardrails

- Stage **10 → 20 → 40** runs; cap `n_runs` and `max_turns` in the runner.
- **Unique `experiment_id` per batch** so `analysis_experiment.csv` stays clean.
- Use **per-experiment CSV** or **`/api/analysis/compare`** for deltas; ignore runner `analysis.json` for single-batch means (it aggregates the whole DB).

## Residual risks

- Judge and API variance; small *n* per arm.
- Judge “gap” field is qualitative; treat **gap rate** as a diagnostic, not a clinical endpoint.
