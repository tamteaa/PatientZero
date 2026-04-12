# PatientZero Architecture

## Purpose

A simulation framework for identifying gaps in doctor-patient communication at scale. Generators produce realistic patient profiles and medical scenarios — sampled from real clinical and demographic distributions — and the system runs thousands of simulated conversations to surface where doctor explanations fail specific patient populations.

Every simulation belongs to an **Experiment**: a named container that snapshots its own target distribution at creation time, so conclusions drawn from a set of runs are reproducible and comparable across experimental conditions.

## System Overview

```
                         ┌─────────────────────────────────────────────┐
                         │                 Experiment                  │
                         │                                             │
                         │  id, name, created_at                       │
                         │  frozen patient_distribution (snapshot)     │
                         │  frozen doctor_distribution (snapshot)      │
                         │  (future) version, parent_experiment_id,    │
                         │          doctor_prompt_version              │
                         │                                             │
                         │   ┌────────────────┐  ┌───────────────┐     │
                         │   │ Patient        │  │ Doctor        │     │
  Real Data              │   │ Generator      │  │ Generator     │     │
  (NAAL, ACS,            │───▶  causal chain  │  │ causal chain  │     │
   NHIS, RIAS,           │   │ (age→edu→lit)  │  │ (setting→tp)  │     │
   CAHPS,                │   └────────┬───────┘  └───────┬───────┘     │
   psych lit.)           │            │                  │             │
                         │            ▼                  ▼             │
                         │       ┌──────────────────────────────┐      │
                         │       │         Simulation           │      │
                         │       │  DoctorAgent ↔ PatientAgent  │      │
                         │       │  (belongs to this experiment)│      │
                         │       └────────────┬─────────────────┘      │
                         │                    │                        │
                         │                    ▼                        │
                         │       ┌──────────────────────────────┐      │
                         │       │     JudgeAgent (evaluation)  │      │
                         │       │  comprehension · recall ·    │      │
                         │       │  reasoning · explanation ·   │      │
                         │       │  interaction · conf-gap      │      │
                         │       └────────────┬─────────────────┘      │
                         │                    │                        │
                         │                    ▼                        │
                         │       ┌──────────────────────────────┐      │
                         │       │   Coverage & Analysis        │      │
                         │       │  (scoped to this experiment) │      │
                         │       │                              │      │
                         │       │  Coverage % = Σ target prob  │      │
                         │       │   of cells hit ≥ 1 time      │      │
                         │       │  Cell = (literacy, anxiety,  │      │
                         │       │    age, empathy, verbosity)  │      │
                         │       │  Effect sizes, worst combos  │      │
                         │       └──────────────────────────────┘      │
                         └─────────────────────────────────────────────┘
                                            │
                                            ▼
                          ┌──────────────────────────────┐
                          │       Feedback Loop          │
                          │  OptimizationTarget + stub   │
                          │  + manual Kimi batch runner  │
                          │                              │
                          │  Identify failure modes →    │
                          │  refine doctor prompt →      │
                          │  spawn Experiment v2 with    │
                          │  same frozen distribution →  │
                          │  compare v1 vs v2 scores     │
                          └──────────────────────────────┘
```

## Data Model

Persistent entities (SQLite, WAL mode):

| Entity | Key fields | Notes |
|---|---|---|
| `experiments` | id, name, **patient_distribution_json**, **doctor_distribution_json**, created_at | Distributions are **snapshots** — edits to module-level baselines do not affect prior experiments. |
| `simulations` | id, **experiment_id** (FK, cascade), persona_name, scenario_name, model, state, config_json, duration_ms | Every sim belongs to exactly one experiment. `config_json` stores the sampled patient/doctor/scenario for later coverage bucketing. |
| `simulation_turns` | simulation_id, turn_number, role, agent_type, content, duration_ms | Per-turn log of the conversation. |
| `evaluations` | simulation_id, judge_results_json | Judge outputs cached per simulation. |
| `sessions`, `turns` | — | Unrelated chat-playground persistence. |

Distributions are modeled as frozen dataclasses (`Distribution`, `ConditionalDistribution`, `PatientDistribution`, `DoctorDistribution`) with `from_dict` / `asdict` round-trip so they can be JSON-serialized into the experiment row and reconstructed on load.

## Coverage Metric

Defined per experiment. A "cell" is the joint of five observable traits: `(literacy, anxiety, age_bucket, empathy, verbosity)` — up to 324 cells under the baseline distributions.

- **Default target (Monte Carlo)** — `GET /api/experiments/{id}/coverage` estimates each cell’s target mass by drawing many `(patient, doctor)` profile pairs through the same **StaticPatientGenerator** / **StaticDoctorGenerator** chains as the simulator (default 100k samples). That matches the **empirical joint** the product actually samples (correlations preserved).
- **Legacy target (`target_method=independence`)** — product of one-dimensional marginals (treats the five traits as independent).
- **Coverage %** = sum of target mass on cells hit ≥ 1 time by completed simulations in the experiment.
- **Distribution match** = `1 − TVD` between the target cell distribution and the empirical distribution of completed sims (diagnostic).
- **Estimated total needed** = `ceil(1 / min_p)` over cells with target probability ≥ 1%. "Enough simulations to expect every non-rare cell to be hit at least once."

**Reproducible sampling:** experiments may set optional **`sampling_seed`** and a monotonic **`sample_draw_index`**; each new simulation draw uses a deterministic RNG stream (`core/sampling.stable_rng`) so runs replay when the seed and ordering are unchanged.

## Research Value

The framework scales identification of doctor communication failures beyond what is possible with real patients. Real clinical and demographic data feeds the generators to ensure realistic inputs. The Experiment container guarantees that every set of runs is attached to a frozen, reproducible target population — necessary preconditions for the feedback loop, where a refined doctor prompt (Experiment v2) can be compared apples-to-apples against a baseline (v1) sampled from identical distributions.
