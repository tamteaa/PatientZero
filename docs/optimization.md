# Optimization

Optimization is how an experiment's prompts get better over time. You run a batch of simulations, the judge scores them, and then the optimizer proposes a new set of prompts that should score higher on the dimensions you care about. If a candidate actually beats the baseline, it becomes the experiment's new current target.

## What gets optimized

The unit of optimization is an **`OptimizationTarget`** — a bundle of named prompt strings (doctor prompt, patient prompt, sometimes more) that get co-optimized as a set. Targets are versioned and immutable: every cycle produces a new target row with a `parent_id` pointing at the one it was evolved from. Nothing is ever edited in place.

## What it optimizes *for*

You don't have to optimize for "the judge score" — you pick a weighted combination of judge dimensions via an `OptimizationMetric`. A single-dimension example is `{"comprehension_score": 1.0}`; a multi-dimension example might weight comprehension heavily but still include interaction quality as a tiebreaker. The metric is also what's used to rank failure cases when building the signal.

## The feedback signal

Optimization doesn't look at prompts in isolation — it looks at evidence from recent runs. The service layer assembles a **`FeedbackSignal`** before handing off to the optimizer:

- **Mean scores per judge dimension** across every completed evaluation for this experiment. Gives the optimizer a sense of absolute performance.
- **Worst cases** — the `k` simulations with the lowest metric scores, each carried as a `FailureCase` (scenario, patient traits, full transcript, scores, judge justification). These are the concrete examples a DSPy-style optimizer needs to reason about what's actually failing.

Two seeding modes control where the signal's failure cases come from:

- **`HISTORICAL_FAILURES`** — reuse existing low-scoring runs. Cheap; uses data you already have.
- **`FRESH_TRIALS`** — run new simulations to generate cases. Slower but avoids baking in whatever bias the old prompts produced.

## The optimizer itself

The pure part of the loop is `core/feedback/feedback.py::Feedback`. It takes an `OptimizationRequest` (current target + signal + config) and returns an `OptimizationResult` (new target + baseline + all candidates + improvement delta). No DB, no persistence, no FastAPI — just signal in, result out.

The current implementation is a stub that fabricates monotonic candidate scores around a signal-derived baseline. The real optimizer will plug DSPy in here — start from `core/llm/dspy_adapter.py` and replace `Feedback.run` when ready. The service layer is already designed for it: everything around the pure class (signal building, template validation, persistence, pointer flip) stays unchanged.

## Safety rails

Before anything gets persisted, `validate_optimization_prompts` checks that the candidate's templates still contain the exact `.format()` field names the simulation stack needs to render them (`profile`, `scenario`, `style`, `style_instructions` for doctor; `profile` for patient). A DSPy run that "improves" a prompt by dropping `{profile}` would break every subsequent simulation — the validator catches that before the pointer flips.

Persisting the winner and flipping `current_optimization_target_id` happen in a single transaction on the optimization-targets repository. A GET against the experiment from the frontend cannot observe a half-written state where the new row exists but the pointer hasn't moved yet.

## What an optimize run returns

The `OptimizationResult` carries everything the UI needs to show a before/after:

- The new (winning) target, with its parent pointer intact
- The baseline — the current target and its measured score
- Every candidate that was considered, with individual scores
- The improvement delta
- The signal that was used, so the UI can show "we considered N simulations and these were the worst K"

The Experiments page renders this directly. There's no separate optimization-history endpoint; the parent-id chain on `OptimizationTarget` is the history.
