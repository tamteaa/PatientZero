# Optimization

The feedback loop that makes prompts better over time: run simulations,
judge them, find failures, propose improved prompts, keep the winner.

## The Loop

```
  ┌──────────────────────────────────────────────────────┐
  │                                                      │
  ▼                                                      │
Experiment.run(n)                                        │
  │                                                      │
  ▼                                                      │
Judge scores each sim                                    │
  │                                                      │
  ▼                                                      │
FeedbackService.optimize()                               │
  │                                                      │
  ├─ collect FeedbackTraces (profiles + transcript       │
  │    + scores + justification)                         │
  │                                                      │
  ├─ pass traces to Feedback optimizer                   │
  │    → proposes new prompt templates                   │
  │                                                      │
  ├─ persist new OptimizationTarget                      │
  │    (parent_id → previous target)                     │
  │                                                      │
  └─ flip experiment.current_optimization_target_id ─────┘
       (atomic with target insert)
```

## What Gets Optimized

An **OptimizationTarget** — a `dict[str, str]` mapping agent name to
prompt template. Targets are versioned and immutable:

```
  target_v0 ◄── target_v1 ◄── target_v2
  (seed)        (optimized)    (optimized)
                                    ▲
                     experiment.current_optimization_target_id
```

Each cycle inserts a new row. Nothing is edited in place. The
`parent_id` chain is the full optimization history.

## The Feedback Signal

`FeedbackService` assembles a list of `FeedbackTrace` objects — one per
completed simulation with its profiles, transcript, scores, and judge
justification. These are the concrete examples the optimizer reasons over.

## The Optimizer

`core/feedback/feedback.py::Feedback` — pure function, no DB, no FastAPI.

```
Input:  OptimizationRequest (current_target + traces)
Output: OptimizationResult  (new_target + previous_target + rationale)
```

## What optimize() Returns

`OptimizationResult` carries everything the UI needs:

| Field | What |
|---|---|
| `new_target` | Winning prompt bundle (with parent_id intact) |
| `previous_target` | The target it was compared against |
| `rationale` | Why the changes were made |
| `traces_considered` | How many sims informed the decision |

## Comparing Generations

Since every simulation records which `optimization_target_id` it ran
under, you can partition results by generation:

```python
v0_scores = exp.scores(optimization_target_id=target_v0.id)
v1_scores = exp.scores(optimization_target_id=target_v1.id)
# {'comprehension': 3.2} vs {'comprehension': 4.1}

exp.history()  # [target_v0, target_v1, target_v2] — full lineage
```
