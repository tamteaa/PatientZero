# Experiments

An **experiment** is a named, persistent container for a batch of simulations that share the same sampling distributions and the same current set of prompts. It's the unit you iterate on: you set up an experiment, run N simulations against it, look at the scores, and then either optimize the prompts or fork the experiment with different distributions.

## Why it exists

Without experiments, every simulation is a one-off — you can't compare runs, you can't track whether prompt changes helped, and you can't ask "what's the mean comprehension score for anxious low-literacy patients under this doctor prompt?" The experiment is the join key that makes those questions answerable.

It also pins reproducibility. An experiment owns a `sampling_seed` and a monotonic `sample_draw_index`, so running 100 simulations today and 100 more tomorrow gives you 200 distinct but deterministic samples rather than two overlapping sets.

## What it owns

- **Sampling distributions** — one per agent (patient, doctor). These are the joint distributions over traits; every new simulation draws its profiles from here.
- **A lineage of optimization targets** — every optimize cycle produces a new target row linked to its parent. The experiment has a single `current_optimization_target_id` pointer that decides which prompts new simulations use.
- **All simulations and evaluations ever run against it** — partitioned by `optimization_target_id` so you can ask "how did the old prompts perform vs. the new ones" without re-running anything.

## The lifecycle

1. **Create** — give it a name and the distributions you want. The repository seeds an initial optimization target from the default doctor/patient prompts and sets it as current.
2. **Run** — call `run(n)`. Each simulation draws its own profiles from a per-sample RNG (derived from the experiment seed + draw index), executes the doctor/patient/judge loop, and persists a `SimulationRecord` + `EvaluationRecord`. Concurrency is bounded by a semaphore.
3. **Inspect** — `scores()` averages judge dimensions across evaluations; `coverage()` reports which regions of the distribution have actually been sampled; `simulations()` can filter by target so you can compare generations.
4. **Optimize** — hands the experiment to `FeedbackService`, which builds a signal from recent evaluations and returns an `OptimizationResult`. If a candidate wins, the experiment's `current_optimization_target_id` moves forward atomically.
5. **Fork** — produces a new experiment with reweighted or replaced distributions. Useful for asking "what if the patient pool were skewed toward low literacy" without losing the baseline.

## Important invariants

- **Names are unique.** Creating an experiment with an existing name is an error — use `Experiment.load(name)` to re-open.
- **Targets are immutable.** Optimization never mutates prompts in place; it inserts a new row and moves the pointer. This means `simulations(optimization_target=...)` can reconstruct any past generation's results cleanly.
- **The current-target pointer and the target insert happen in one transaction.** A concurrent reader cannot observe a half-flipped state.
- **Self-healing on load.** Experiments that predate the seed-initial-target code will get a target minted and the pointer set on the next optimize call.

## What it is not

The experiment is a coordination layer, not a domain engine. It doesn't know how to run a turn, doesn't know how to build a prompt, and doesn't know how to optimize. It holds the pieces together and delegates:

- Turn execution → `SimulationService` and `Simulation`
- Prompt rendering → the agent classes + `core/feedback/template_validation.py`
- Optimization → `FeedbackService` + `Feedback`
- Persistence → the four repositories under `core/repositories/`
