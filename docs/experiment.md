# Experiments

An experiment is a named container for simulations that share the same
agents, distributions, judge, and current prompts. It's the unit you
iterate on.

## Quick Start

```python
from core.agent import Agent
from core.distribution import Distribution, Conditional
from core.experiment import Experiment
from core.types import ExperimentConfig, JudgeConfig
from core.repositories import RepoSet
from core.db import Database

db = Database("experiment.db")
repos = RepoSet(db)

config = ExperimentConfig(
    name="baseline-v1",
    agents=(
        Agent("doctor", DOCTOR_PROMPT, doctor_distribution),
        Agent("patient", PATIENT_PROMPT, patient_distribution),
    ),
    judge=JudgeConfig(
        rubric={"comprehension": "Did the patient understand?"},
        instructions="Score 1-5.",
    ),
    model="kimi:kimi-k2.5",
    seed=42,
    max_turns=4,
)

exp = Experiment(config, repos)     # creates DB row + seeds initial target
sim_ids = await exp.run(n=20)       # 20 concurrent sims, judge-evaluated
print(exp.scores())                 # {'comprehension': 3.7}
print(exp.coverage())               # CoverageReport(coverage_pct=0.42, ...)

result = await exp.optimize()       # propose better prompts, persist if improved
sim_ids = await exp.run(n=20)       # run again with new prompts
print(exp.scores())                 # {'comprehension': 4.1}
```

## Lifecycle

```
  create          run(n)          inspect          optimize         run(n) again
    │               │                │                │                │
    ▼               ▼                ▼                ▼                ▼
┌────────┐   ┌───────────┐   ┌────────────┐   ┌───────────┐   ┌───────────┐
│ Config │──▶│ n Sims    │──▶│ scores()   │──▶│ new       │──▶│ n Sims    │
│ + seed │   │ + judge   │   │ coverage() │   │ target    │   │ w/ new    │
│ + t0   │   │ evals     │   │ history()  │   │ persisted │   │ prompts   │
└────────┘   └───────────┘   └────────────┘   └───────────┘   └───────────┘
```

## Reproducibility

Each experiment has a `seed` and a monotonic `sample_draw_index`. Every
`run()` call bumps the index and derives a per-simulation RNG via
`stable_rng(seed, draw_index)`. Running 50 sims today and 50 tomorrow
gives 100 distinct but deterministic samples.

## Invariants

- **Names are unique** — duplicate names raise on create; use `Experiment.load(name, repos)` to reopen.
- **Targets are immutable** — optimization inserts a new row, never mutates. `simulations(optimization_target=...)` partitions by generation.
- **Pointer flip is transactional** — inserting a new target and updating `current_optimization_target_id` happen atomically.
