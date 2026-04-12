# Architecture

## What PatientZero Does

LLM agents simulate doctor-patient conversations about medical results.
A judge agent scores how well the doctor communicated. Run thousands of
these, find where explanations fail, improve the prompts, repeat.

## System Flow

```
  ExperimentConfig
  ┌─────────────────────────────────────────────────────────┐
  │  agents:  (doctor, patient)    each with a Distribution │
  │  judge:   rubric + instructions                         │
  │  model:   "kimi:kimi-k2.5"                              │
  │  seed:    42                                            │
  └────────────────────────┬────────────────────────────────┘
                           │
                           ▼
                    Experiment.run(n=50)
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼        (concurrent, semaphore-bounded)
         Simulation   Simulation   Simulation
              │            │            │
              │   ┌────────┘            │
              ▼   ▼                     ▼
        ┌──────────────┐         ┌──────────────┐
        │  Distribution │         │  Distribution │
        │  .sample()    │         │  .sample()    │
        │  → profiles   │         │  → profiles   │
        └──────┬───────┘         └──────┬───────┘
               │                        │
               ▼                        ▼
        ┌──────────────────────────────────────┐
        │         AgentRuntime (doctor)         │
        │              ↕ turns                  │
        │         AgentRuntime (patient)        │
        │         (up to max_turns)             │
        └──────────────┬───────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────┐
        │   Judge.evaluate(transcript)          │
        │   → scores per rubric dimension       │
        └──────────────┬───────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────┐
        │   Coverage & Scores                   │
        │   "which trait combos were tested?"    │
        │   "where do scores drop?"             │
        └──────────────┬───────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────┐
        │   FeedbackService.optimize()          │
        │   collect failure cases →              │
        │   propose new prompts →                │
        │   persist winning OptimizationTarget   │
        │   → repeat from Experiment.run()       │
        └──────────────────────────────────────┘
```

## Database (SQLite, WAL mode)

```
experiments
  id | config_json | current_optimization_target_id | sample_draw_index | created_at
       └── entire ExperimentConfig serialized here

optimization_targets
  id | experiment_id (FK) | kind | prompts_json | parent_id (FK, self) | created_at

simulations
  id | experiment_id (FK) | optimization_target_id (FK) | config_json | state | duration_ms | created_at

simulation_turns
  id | simulation_id (FK) | turn_number | role | agent_type | content | duration_ms

evaluations
  id | simulation_id (FK) | experiment_id (FK) | judge_results_json

sessions / turns  ← separate chat-playground tables, not part of experiment graph
```

## Key Files

```
core/agent.py          Agent dataclass (name, prompt, distribution, model)
core/distribution.py   Distribution DAG (Marginal, Conditional, topo-sort)
core/judge.py          Judge (rubric → system prompt → evaluate transcript)
core/experiment.py     Experiment facade (run, optimize, coverage, scores)
core/simulation.py     Simulation state machine (run/step/pause/resume/stop)
core/sampling.py       stable_rng(seed, draw_index) → deterministic Random
core/analysis/         coverage.py — Monte Carlo coverage over trait cells
core/services/         feedback.py — FeedbackService orchestration
core/agents/base.py    AgentRuntime (LLM wrapper: respond / stream)
core/llm/              Provider ABC + factory + mock/kimi/claude/openai/local
core/repositories/     experiments, simulations, evaluations, optimization_targets
core/types/            Dataclasses & enums, re-exported from __init__
core/examples/medical/ Full working config with US patient/doctor distributions
```
