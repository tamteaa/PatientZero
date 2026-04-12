# Domain Models

The shapes that everything else in PatientZero is built on. All dataclasses live under `core/types/` and are re-exported from `core/types/__init__.py`. Persistence schema lives in `core/db/schema.sql`.

## Entity relationships

```
Experiment ──1:N──▶ OptimizationTarget ──parent_id──▶ OptimizationTarget
     │                     ▲
     │                     │ (current_optimization_target_id)
     │                     │
     └──1:N──▶ Simulation ──1:N──▶ SimulationTurn
                   │
                   └──1:N──▶ Evaluation ──N── JudgeResult (JSON)
```

`Session` / `Turn` are a separate, older table pair used for the free-form chat UI and are not part of the experiment graph.

---

## Experiment

`core/types/records.py::Experiment`

The top-level container for a batch of simulations that share sampling distributions and an active optimization target.

| field                             | type                    | notes                                                                 |
| --------------------------------- | ----------------------- | --------------------------------------------------------------------- |
| `id`                              | `str`                   | UUID                                                                  |
| `name`                            | `str`                   |                                                                       |
| `patient_distribution`            | `PatientDistribution`   | joint distribution over patient traits                                |
| `doctor_distribution`             | `DoctorDistribution`    | joint distribution over doctor traits                                 |
| `current_optimization_target_id`  | `str \| None`           | which target new simulations use                                      |
| `sampling_seed`                   | `int \| None`           | set for reproducible draws                                            |
| `sample_draw_index`               | `int`                   | incremented each draw so re-runs are deterministic but non-repeating  |

`to_dict()` accepts a `counts` block (`total`, `completed`, `running`, `error`, `evaluated`) that the repository populates at read time — it isn't stored on the row.

## Distributions

`core/types/distribution.py`

Sampling is done via causal chains of discrete distributions. `Distribution.weights` must sum to 1.0 (validated in `__post_init__`). `ConditionalDistribution` is `P(child | parent)`: one `Distribution` per parent value.

**Patient chain:**
```
age → education → literacy → tendency
age → anxiety
```

**Doctor chain:**
```
setting → time_pressure → verbosity
empathy → comprehension_checking
```

Each `XDistribution` dataclass exposes a `from_dict` classmethod; distributions are persisted as JSON blobs on the `experiments` row (`patient_distribution_json`, `doctor_distribution_json`).

## OptimizationTarget

`core/types/feedback.py::OptimizationTarget`

A versioned bundle of prompt strings that gets co-optimized by the feedback loop.

| field           | type            | notes                                              |
| --------------- | --------------- | -------------------------------------------------- |
| `id`            | `str`           |                                                    |
| `experiment_id` | `str`           | targets belong to exactly one experiment           |
| `kind`          | `str`           | `"doctor_prompts"`, `"doctor_and_patient"`, etc.   |
| `prompts`       | `dict[str,str]` | prompt name → template string                      |
| `parent_id`     | `str \| None`   | lineage — points at the target this was evolved from |

Targets are immutable. Each optimization cycle inserts a new row; `Experiment.current_optimization_target_id` moves forward if the new candidate beats the baseline.

## Simulation

`core/types/records.py::SimulationRecord`

One doctor/patient/judge run. Links to the experiment and (optionally) the optimization target active when it ran, so results can be partitioned by target.

Key fields: `id`, `experiment_id`, `persona_name`, `scenario_name`, `model`, `state` (`running` / `completed` / `error`), `config_json`, `duration_ms`, `optimization_target_id`.

## SimulationTurn

`core/types/records.py::SimulationTurnRecord`

Append-only per-turn log. `role` is the chat role (`user`/`assistant`); `agent_type` identifies which agent produced it (`doctor`/`patient`). `duration_ms` is per-turn latency.

## Evaluation & JudgeResult

`core/types/records.py::EvaluationRecord`, `core/types/judge_result.py::JudgeResult`

`EvaluationRecord` is a thin row that stores a list of `JudgeResult`s as JSON (`judge_results_json`). Keeping judge output denormalized means rubric shape can change without schema migrations. `experiment_id` is duplicated on the row to allow direct aggregation without joining through `simulations`.

---

## Feedback-loop value types

These live alongside `OptimizationTarget` in `core/types/feedback.py` and are in-memory only — they are the inputs and outputs of one optimize run, not persisted entities.

- **`OptimizationMetric`** — weighted combination of `JudgeResult.scores` dimensions. `score(judge_result)` returns the weighted sum.
- **`OptimizationConfig`** — knobs for one run: `metric`, `seeding_mode` (`HISTORICAL_FAILURES` or `FRESH_TRIALS`), `num_candidates`, `trials_per_candidate`, `worst_cases_k`.
- **`FailureCase`** — one low-scoring simulation carried as DSPy context (scenario, patient traits, transcript, scores, judge justification).
- **`FeedbackSignal`** — aggregated evidence feeding into optimization: `simulations_considered`, `mean_scores`, `worst_cases`.
- **`OptimizationRequest`** = `current_target` + `signal` + `config`.
- **`CandidateScore`** — a target plus its measured `mean_score` and `trial_count`.
- **`OptimizationResult`** — `new_target`, `baseline`, all `candidates`, `improvement`, and the `signal` used. This is what the feedback API returns and what the Experiments UI renders.

---

## Chat (non-experiment) entities

`SessionRecord` and `TurnRecord` back the free-form chat UI. They have their own tables (`sessions`, `turns`) and are intentionally decoupled from experiments — no foreign keys into the experiment graph.
