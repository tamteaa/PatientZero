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

### Blocker — sim runner does NOT yet read the current target

The simulate route still calls `build_doctor_prompt` / `build_patient_prompt` from `core/agents/prompts.py` directly. This means new simulations are **not actually using** whatever prompt the optimizer writes. The loop is persisted but inert.

- [ ] **Wire `SimulationService.create_and_start` to read the experiment's current target.** Load `current_optimization_target_id`, fetch the target row, and pass its `prompts["doctor"]` / `prompts["patient"]` into the agent construction. If the target's templates are the ones in `prompts.py`, behavior is unchanged; if they were modified by optimize, behavior changes.
- [ ] Decide how the template is rendered with per-run profile data. The stored template is a string; `build_doctor_prompt` currently does `.format(...)` with profile/scenario/style fields. Either:
  - (a) store templates as format strings and keep `.format(...)` at sim-run time, OR
  - (b) store fully-rendered prompts (no placeholders) and change the signature of `build_doctor_prompt` to take the template as a parameter.
  (a) is simpler; (b) gives the optimizer more freedom to change structure. Pick (a) for now.

### Next — replace the stub with DSPy

- [ ] Add `dspy` dependency (`uv add dspy`). Pin a version.
- [ ] LM adapter: bridge `LLMProvider` → `dspy.LM` in `core/llm/dspy_adapter.py`. Must support the mock provider for cheap dev runs.
- [ ] Replace the body of `Feedback.run` in `core/feedback/feedback.py` with a real DSPy pipeline:
  - Signature with one output field per prompt name in `current_target.prompts`
  - Metric function uses `OptimizationMetric.score()` on the judge result (reuse existing `JudgeAgent`)
  - Seeding mode switch: `HISTORICAL_FAILURES` replays the signal's `worst_cases` as DSPy examples; `FRESH_TRIALS` samples new examples from the experiment's distributions
  - Return the real `OptimizationResult` with actual candidates + scores
- [ ] Caching: memoize metric calls by `hash(prompt + scenario + patient_traits)` to avoid re-running identical mini-sims across optimizer rounds
- [ ] Concurrency cap: add `max_concurrent_optimizations: int = 1` to `AppSettings`, enforce in the optimize route

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
- [ ] Stamp `optimization_target_id` on each completed simulation so historical "score vs target" plots are possible. Currently deferred because the user said no need for this, but revisit after DSPy lands — it becomes much more valuable once the target actually changes.

## Dashboard

- [ ] Gap-filling run mode: when coverage is below target, the Run button preferentially samples under-covered cells instead of drawing from the full distribution.
- [ ] Score-over-time chart: plot the rolling mean comprehension score across sims within an experiment, broken by `optimization_target_id` once that's stamped.
