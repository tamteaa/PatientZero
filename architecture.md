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
                          │        (not yet built)       │
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

Defined per experiment. A "cell" is the joint of five observable traits: `(literacy, anxiety, age_bucket, empathy, verbosity)` — 324 cells under the baseline distributions.

- **Target probability** per cell is the product of the marginals of those five traits under the experiment's frozen distributions. (First-order approximation: treats the five traits as independent for coverage bookkeeping. The true joint has correlations via the causal chain in the generators, but the simplification is sufficient for "have I sampled enough of the population to draw conclusions" questions.)
- **Coverage %** = sum of target probabilities of cells that have been hit ≥ 1 time by completed simulations in the experiment.
- **Estimated total needed** = `ceil(1 / min_p)` over cells with target probability ≥ 1%. "Enough simulations to expect every non-rare cell to be hit at least once."

Both numbers are recomputed on demand by `GET /api/experiments/{id}/coverage`, which parses each simulation's `config_json` to locate its cell.

## Research Value

The framework scales identification of doctor communication failures beyond what is possible with real patients. Real clinical and demographic data feeds the generators to ensure realistic inputs. The Experiment container guarantees that every set of runs is attached to a frozen, reproducible target population — necessary preconditions for the feedback loop, where a refined doctor prompt (Experiment v2) can be compared apples-to-apples against a baseline (v1) sampled from identical distributions.
