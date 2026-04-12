# Domain Models

All types live under `core/types/` (re-exported from `core/types/__init__.py`)
except `Agent`, `Distribution`, and `Judge` which are top-level in `core/`.

## Entity Graph

```
Experiment ──1:N──▶ OptimizationTarget ──parent_id──▶ OptimizationTarget
     │                     ▲
     │                     │ current_optimization_target_id
     │
     └──────1:N──▶ Simulation ──1:N──▶ SimulationTurn
                       │
                       └──1:N──▶ Evaluation ──embeds──▶ [JudgeResult]
```

---

## Distribution

`core/distribution.py` — a DAG of discrete trait nodes, topo-sorted at
construction, sampled in causal order.

```
                  Marginal              Conditional
               ┌────────────┐       ┌───────────────────┐
               │ weights:    │       │ parent: "age"     │
               │  young: 0.3 │       │ table:            │
               │  old:   0.7 │       │   young:          │
               └────────────┘       │     low:  0.2     │
                                    │     high: 0.8     │
                                    │   old:            │
                                    │     low:  0.6     │
                                    │     high: 0.4     │
                                    └───────────────────┘
```

Constructing a distribution:

```python
from core.distribution import Distribution, Conditional

patient = Distribution(
    age={"young": 0.3, "old": 0.7},
    literacy=Conditional("age", {
        "young": {"low": 0.2, "high": 0.8},
        "old":   {"low": 0.6, "high": 0.4},
    }),
    anxiety=Conditional("age", {
        "young": {"calm": 0.7, "anxious": 0.3},
        "old":   {"calm": 0.4, "anxious": 0.6},
    }),
)

patient.topo_order   # ('age', 'literacy', 'anxiety')
patient.sample(rng)  # {'age': 'old', 'literacy': 'low', 'anxiety': 'anxious'}
```

Sampling walks topo order — conditionals read already-sampled parent values.
Constraints pin traits: `patient.sample(rng, literacy="low")` forces literacy
and samples the rest normally.

Key methods: `sample()`, `marginal(trait)`, `cells(*traits)`, `replace()`,
`reweight()`. Serialized via `distribution_to_dict` / `distribution_from_dict`.

---

## Agent

`core/agent.py` — binds a name, prompt template, and distribution together.

```python
from core.agent import Agent

doctor = Agent(
    name="doctor",
    prompt="You are a {setting} doctor. Explain {scenario} to the patient.\n{profile}",
    distribution=doctor_dist,
    model="kimi:kimi-k2.5",   # optional per-agent override
)

traits = doctor.sample(rng)            # {'setting': 'ER', 'verbosity': 'terse', ...}
prompt = doctor.render({**traits, "scenario": "CBC results"})
doctor.prompt_fields                   # frozenset({'setting', 'scenario', 'profile'})
```

---

## Judge

`core/judge.py` — evaluates a transcript against a rubric.

```python
judge = Judge(
    rubric={"comprehension": "Did the patient understand?", "clarity": "Was the doctor clear?"},
    instructions="Score 1-5. Be strict on medical accuracy.",
    model="kimi:kimi-k2.5",
)

result = await judge.evaluate(transcript)
# JudgeResult(model="kimi-k2.5", scores={"comprehension": 4, "clarity": 3}, justification="...")
```

Builds a system prompt from the rubric, asks the LLM for JSON `{scores, justification}`.

---

## ExperimentConfig → ExperimentRecord

`core/types/records.py`

```
ExperimentConfig (user input)         ExperimentRecord (persisted)
┌──────────────────────────────┐     ┌──────────────────────────────────┐
│ name: str                    │     │ id: str                          │
│ agents: (Agent, ...)         │     │ created_at: str                  │
│ judge: JudgeConfig           │     │ config: ExperimentConfig         │
│ model: str                   │     │ current_optimization_target_id   │
│ seed: int | None             │     │ sample_draw_index: int           │
│ max_turns: int = 8           │     └──────────────────────────────────┘
│ num_optimizations: int = 0   │
└──────────────────────────────┘
```

`JudgeConfig`: `rubric: dict[str, str]`, `instructions: str`, `model: str | None`.

---

## OptimizationTarget

`core/types/feedback.py` — immutable, versioned prompt bundle.

```
 target_v0 ◄──parent_id── target_v1 ◄──parent_id── target_v2
 (seed)                   (optimized)               (optimized)
                                                         ▲
                                          experiment.current_optimization_target_id
```

Fields: `id`, `experiment_id`, `kind`, `prompts: dict[str, str]`,
`parent_id`, `created_at`.

`prompts` maps agent name → prompt template string. Targets are never mutated;
each optimization cycle inserts a new row.

---

## Simulation & SimulationTurn

`core/types/records.py`

`SimulationRecord`: `id`, `experiment_id`, `optimization_target_id`,
`config_json` (sampled profiles + scenario), `state` (running/completed/error),
`duration_ms`.

`SimulationTurnRecord`: `simulation_id`, `turn_number`, `role` (user/assistant),
`agent_type` (doctor/patient), `content`, `duration_ms`.

---

## Evaluation & JudgeResult

`EvaluationRecord` stores a list of `JudgeResult`s as JSON. Keeping judge
output denormalized means rubric shape can change without schema migrations.

`JudgeResult`: `model`, `scores: dict[str, float | None]`, `justification`.

---

## Feedback Value Types

In-memory only (not persisted), used during one optimize cycle:

| Type | Role |
|---|---|
| `FeedbackTrace` | One sim's profiles + transcript + scores + justification |
| `OptimizationResult` | new_target + previous_target + rationale + traces_considered |
