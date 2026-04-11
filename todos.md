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

- [ ] Add `dspy` dependency (`uv add dspy`). Pin a version.
- [ ] LM adapter: bridge `LLMProvider` → `dspy.LM` in `core/llm/dspy_adapter.py`. Must support the mock provider for cheap dev runs.
- [ ] Replace the body of `Feedback.run` in `core/feedback/feedback.py` with a real DSPy pipeline:
  - Signature with one output field per prompt name in `current_target.prompts`
  - Metric function uses `OptimizationMetric.score()` on the judge result (reuse existing `JudgeAgent`)
  - Seeding mode switch: `HISTORICAL_FAILURES` replays the signal's `worst_cases` as DSPy examples; `FRESH_TRIALS` samples new examples from the experiment's distributions
  - Return the real `OptimizationResult` with actual candidates + scores
- [ ] Caching: memoize metric calls by `hash(prompt + scenario + patient_traits)` to avoid re-running identical mini-sims across optimizer rounds
- [x] **Concurrency cap** — `AppSettings.max_concurrent_optimizations` (default `1`); optimize route returns **409** if the semaphore cannot be acquired (non-blocking).

### UI polish (after DSPy lands)

- [ ] Config dialog before optimize: metric weights sliders, seeding mode radio, num_candidates + trials_per_candidate number inputs
- [ ] Optimization history card on the Experiments page: list of all targets in the chain (lineage via `parent_id`), with mean score at the time of each
- [ ] View-current-prompt panel: show the raw `prompts["doctor"]` and `prompts["patient"]` strings for the current target so you can inspect what the optimizer produced
- [ ] SSE progress stream for long-running optimize runs: `GET /api/experiments/{id}/optimize/stream`
- [ ] "Revert to target" action on any historical target row → updates `current_optimization_target_id` without losing the newer rows

---

## Coverage metric refinements

- [ ] Replace the product-of-marginals independence assumption with Monte-Carlo-sampled empirical targets: sample 100k (patient, doctor) pairs from the experiment's generator, use empirical cell frequencies as the target. Cheap, principled, exactly correct under the joint the generator actually produces.
- [ ] Add a distribution-match score alongside the hit-rate coverage: `1 − TVD(empirical, target)` clipped to [0,1].
- [ ] Per-cell depth breakdown: `count / expected_count` per cell, surfaced as an overlay on the Dashboard coverage bar.

## Generator gaps

- [ ] Primary language / LEP as a patient trait. Major real-world driver of comprehension failure, currently unmodeled.
- [ ] Cognitive load / working memory as a patient trait. Independent of literacy, affects recall.
- [ ] Prior familiarity with condition (e.g. new vs established diabetic) as a patient trait. Affects baseline understanding.

## Reproducibility

- [ ] Per-experiment `seed` field so the sampling draw is exactly reproducible across runs.
- [x] Stamp **`optimization_target_id` in simulation `config_json`** at creation (see Feedback Loop / manual batch sections). Optional: add a dedicated DB column later for indexing.

## Dashboard

- [ ] Gap-filling run mode: when coverage is below target, the Run button preferentially samples under-covered cells instead of drawing from the full distribution.
- [ ] Score-over-time chart: plot the rolling mean comprehension score across sims within an experiment, broken by `optimization_target_id` once that's stamped.
