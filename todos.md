# PatientZero — TODOs

## Feedback Loop

The feedback loop is scaffolded end-to-end but the optimization step is stubbed. The shape is: each experiment owns a chain of `OptimizationTarget` rows (each a named set of prompts, with `parent_id` lineage). The current target is referenced by `experiments.current_optimization_target_id`. Hitting **Optimize** on an experiment runs the `FeedbackService`, which builds a `FeedbackSignal` from completed + evaluated sims, calls the `Feedback` class (currently stubbed), persists the winning candidate as a new `OptimizationTarget`, and repoints the experiment at it.

### Done

- [x] `OptimizationTarget` table with FK to experiment + self-FK for lineage
- [x] `experiments.current_optimization_target_id` column
- [x] Initial target seeded on experiment creation (uses current `_DOCTOR` / `_PATIENT` templates from `core/agents/prompts.py`)
- [x] Domain types: `OptimizationMetric`, `OptimizationConfig`, `SeedingMode`, `OptimizationTarget`, `FailureCase`, `FeedbackSignal`, `OptimizationRequest`, `CandidateScore`, `OptimizationResult`
- [x] `core/feedback/feedback.py` — pure `Feedback` class with stubbed `run()`
- [x] `core/services/feedback.py` — `FeedbackService` does DB I/O, signal building, persistence
- [x] `POST /api/experiments/{id}/optimize` — accepts `metric_weights`, `seeding_mode`, `num_candidates`, `trials_per_candidate`, `worst_cases_k`
- [x] Frontend: Optimize button on the Experiments page detail pane

### Sim runner + current target (merged)

- [x] **`SimulationService.create_and_start` loads the experiment’s `current_optimization_target`** and passes `prompts["doctor"]` / `prompts["patient"]` into `build_doctor_prompt` / `build_patient_prompt` as optional templates (same `{profile}`, `{scenario}`, … placeholders as `_DOCTOR` / `_PATIENT`). `policy_version` overlays still apply after formatting.
- [x] **API simulate** requires a real `experiments.id`; optional `batch_id` for analysis/compare labels (`config_json.batch_id`). See `evaluations/feedback/RUNBOOK.md`.

### Manual Kimi feedback batches

- [x] CLI `evaluations/feedback/run_feedback_cycle.py` — uses `--experiment-db-id` + `--batch-id`, respects experiment distributions, writes artifacts under `evaluations/feedback/artifacts/<batch_id>/`.
- [x] Evidence write-up: `evaluations/feedback/RECOMMENDATIONS.md` (low-literacy n=10 A/B).
- [x] **`optimization_target_id` in `config_json`** on new simulations (API + CLI batch) and in **analysis CSV export** for downstream charts / grouping.

### Remaining template / optimizer nuances

- [x] **Validate templates before persisting** — `core/feedback/template_validation.py` + `FeedbackService.optimize` raises `400` if doctor/patient prompts lack required `.format` fields (`profile`, `scenario`, `style`, `style_instructions` for doctor; `profile` for patient). DSPy must still output compatible templates or we add a fallback layer later.
- [ ] If DSPy produces **different** placeholder schemes, add an explicit adapter or fallback template (not just validation).

### Next — replace the stub with DSPy

- [x] Add **`dspy-ai`** dependency (pinned in `pyproject.toml`).
- [x] Skeleton `core/llm/dspy_adapter.py` (`get_dspy` / `dspy_available`); **LM bridge** (`LLMProvider` → DSPy) still TODO.
- [ ] Replace the body of `Feedback.run` in `core/feedback/feedback.py` with a real DSPy pipeline:
  - Signature with one output field per prompt name in `current_target.prompts`
  - Metric function uses `OptimizationMetric.score()` on the judge result (reuse existing `JudgeAgent`)
  - Seeding mode switch: `HISTORICAL_FAILURES` replays the signal's `worst_cases` as DSPy examples; `FRESH_TRIALS` samples new examples from the experiment's distributions
  - Return the real `OptimizationResult` with actual candidates + scores
- [ ] Caching: memoize metric calls by `hash(prompt + scenario + patient_traits)` to avoid re-running identical mini-sims across optimizer rounds
- [x] **Concurrency cap** — `AppSettings.max_concurrent_optimizations` (default `1`); optimize route returns **409** if the semaphore cannot be acquired (non-blocking).

### UI polish (after DSPy lands)

- [x] **Optimize options** (collapsible): seeding mode, num_candidates, trials_per_candidate, worst_cases_k, comprehension weight — on Experiments page.
- [ ] Optimization history card on the Experiments page: list of all targets in the chain (lineage via `parent_id`), with mean score at the time of each
- [x] **Current target prompts** collapsible on Experiments page (raw doctor/patient templates).
- [ ] SSE progress stream for long-running optimize runs: `GET /api/experiments/{id}/optimize/stream`
- [x] "Revert to target" — **Use this target** on Experiments page + `POST /api/experiments/{id}/optimization-target/current`

---

## Coverage metric refinements

- [x] Replace the product-of-marginals independence assumption with **Monte Carlo** empirical targets (default on `GET /api/experiments/{id}/coverage`; `target_method=independence` for legacy).
- [x] Add **distribution_match** (`1 − TVD` between target and completed-sim cell empirical).
- [ ] Per-cell depth breakdown: `count / expected_count` per cell, surfaced as an overlay on the Dashboard coverage bar.

## Generator gaps

- [ ] Primary language / LEP as a patient trait. Major real-world driver of comprehension failure, currently unmodeled.
- [ ] Cognitive load / working memory as a patient trait. Independent of literacy, affects recall.
- [ ] Prior familiarity with condition (e.g. new vs established diabetic) as a patient trait. Affects baseline understanding.

## Reproducibility

- [x] Per-experiment **`sampling_seed`** + **`sample_draw_index`** with `PATCH /api/experiments/{id}`; deterministic draws for `POST /api/simulate` and the feedback CLI batch runner.
- [x] Stamp **`optimization_target_id`** on simulations: dedicated **`simulations.optimization_target_id`** column (indexed) plus **`config_json`** mirror at creation (API + CLI).

## Dashboard

- [ ] Gap-filling run mode: when coverage is below target, the Run button preferentially samples under-covered cells instead of drawing from the full distribution.
- [ ] Score-over-time chart: plot the rolling mean comprehension score across sims within an experiment, broken by `optimization_target_id` once that's stamped.
