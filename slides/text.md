# Slide Text & Graphics

Exact content for each slide.

---

## Slide 1 — Title

**PatientZero**

A Framework for Realistic LLM-Driven Patient Simulation at Scale

Surya Mani, Aaron Tamte, Lile Zhang
CS6170 — Spring 2026

---

## Slide 2 — The Problem

**AI is already a de facto health source**

Does the way AI explains medical information, and how users interact
with it, affect comprehension?

**12%** of U.S. adults have proficient health literacy.

**40-80%** of medical information is forgotten immediately after a
doctor visit.

Testing health-communication agents with real patients is slow and
expensive. If synthetic simulations can approximate real behavior,
we iterate faster.

---

## Slide 3 — Why Simulation

**Real patients don't scale**

- 12-16 recruits per study vs hundreds of synthetic personas
- Weeks of recruitment vs minutes of simulation
- One population slice vs the full demographic space
- Can't rerun the same population after changing the intervention — with simulation you can

Simulation doesn't replace human validation. It tells you *what* to validate.

---

## Slide 4 — No Good Methods Exist

**LLM patient simulation is an open problem**

```
Existing approaches                    What's needed
─────────────────────                  ─────────────────────
Traits sampled independently           Correlated traits from real data
  → impossible combinations              → age affects literacy affects behavior

No coverage tracking                   Know which populations you've tested
  → blind spots invisible                → and which you've missed

Manual prompt tuning                   Automated feedback loop
  → read transcripts, guess, rerun       → find failures, propose fixes, measure

Single-score evaluation                Multi-dimensional rubric
  → "good/bad"                           → comprehension, recall, reasoning, ...
```

---

## Slide 5 — The Pivot

**From Proposal to Implementation**

```
PROPOSED                               IMPLEMENTED
─────────────────────                  ─────────────────────
Human participant study         →      LLM simulation framework

- 12-16 real participants              + Scales to hundreds of personas
- 2x2 between-subjects design          + N x M x K condition matrix
- Web tool + survey instruments        + Full-stack research system
- Recruitment-dependent                + No recruitment bottleneck
- Simulation as validation step        + Simulation is the central method
```

We realized the method itself was the missing piece.

---

## Slide 6 — PatientZero: What We Built

**Three core concepts**

**Agent** — a simulated participant with a demographic profile drawn
from a causal trait distribution. Each agent has a prompt template
that adapts to its sampled traits.

**Judge** — a structured evaluator that scores conversations across
multiple dimensions (comprehension, recall, reasoning, explanation
quality, interaction quality). Configurable per experiment.

**Experiment** — a reproducible container. Runs N simulations across
the demographic space, evaluates each one, tracks which populations
have been covered, and optimizes prompts automatically through a
feedback loop.

---

## Slide 7 — Causal Distributions

**Traits are correlated, not independent**

Patient trait DAG:
```
age ──┬──▶ education ──▶ literacy ──▶ tendency
      ├──▶ anxiety
      └──▶ scenario
```

Doctor trait DAG:
```
setting ──▶ time_pressure ──▶ verbosity
empathy ──▶ comprehension_checking
```

A low-literacy patient is more likely to be older, less educated, and
deferential — because real patients are.

Grounded in real data:
- **Patient**: NAAL (literacy given education), NHIS (anxiety given age), US Census
- **Doctor**: RIAS, CAHPS (physician communication patterns)

Traits can be pinned for controlled experiments: "only low-literacy
patients" still samples the rest of the chain realistically.

---

## Slide 8 — System Architecture

```
  ┌─────────────────┐     ┌─────────────────┐
  │ Patient          │     │ Doctor           │
  │ Distribution     │     │ Distribution     │
  │ (causal traits)  │     │ (causal traits)  │
  └────────┬────────┘     └────────┬─────────┘
           │                       │
           ▼                       ▼
  ┌────────────────────────────────────────┐
  │          Simulation Engine             │
  │                                        │
  │   Doctor agent ◄──conversation──▶ Patient agent
  │   (adapts to profile)            (behaves per traits)
  │                                        │
  └────────────────┬───────────────────────┘
                   │
                   ▼
  ┌────────────────────────────────────────┐
  │          Judge Evaluation              │
  │   5 dimensions + justification         │
  └────────────────┬───────────────────────┘
                   │
          ┌────────┴────────┐
          ▼                 ▼
  ┌──────────────┐  ┌──────────────────┐
  │  Coverage    │  │  Feedback Loop   │
  │  Analysis    │  │  find failures → │
  │  (which      │  │  improve prompts │
  │   cells?)    │  │  → re-measure    │
  └──────────────┘  └──────────────────┘
```

---

## Slide 9 — Evaluation

**5 dimensions of medical communication quality**

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Comprehension   │  │ Factual recall  │  │ Applied         │
│                 │  │                 │  │ reasoning       │
│ Overall patient │  │ Key numbers,    │  │ Can they act    │
│ understanding   │  │ terms, action   │  │ on what they    │
│                 │  │ items retained  │  │ were told?      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
┌─────────────────┐  ┌─────────────────┐
│ Explanation     │  │ Interaction     │
│ quality         │  │ quality         │
│                 │  │                 │
│ Clarity,        │  │ Comprehension   │
│ completeness,   │  │ checks,         │
│ accuracy        │  │ adaptation,tone │
└─────────────────┘  └─────────────────┘
```

Grounded in health communication research on what predicts patient
outcomes. Each simulation gets scored across all five with a written
justification.

---

## Slide 10 — The Feedback Loop

**Measure → Diagnose → Intervene → Re-measure**

```
  Run N simulations with current prompts
                 │
                 ▼
  Judge scores each conversation
                 │
                 ▼
  Identify worst-performing cases
  (full transcripts + patient profiles + scores)
                 │
                 ▼
  Optimizer analyzes failures, proposes new prompts
                 │
                 ▼
  New prompts saved as versioned target
  (previous version preserved for comparison)
                 │
                 ▼
  Run N simulations with new prompts
                 │
                 ▼
  Compare generations: did scores improve?
```

Every version of the prompts and its results are preserved.
Generations are always comparable.

---

## Slide 11 — Results

[Bar chart: Baseline vs Intervention across 5 dimensions]
[Radar chart: Baseline vs Intervention overlay]

- Comprehension +6.5 (d=0.81)
- Applied reasoning +6.4 (d=1.12)
- Interaction quality +5.8 (d=0.97)
- Explanation quality +2.1 (d=0.23)

[Confidence-comprehension gap rate bar]
- Baseline: 80%
- Intervention: 27%

The feedback loop identified that low-literacy patients needed more
comprehension checks. The optimized prompt (v2_low_literacy_checks)
measurably improved scores across all dimensions.

Protocol: patient_literacy=low, kimi:kimi-k2.5, n=10 per arm, max_turns=6

---

## Slide 12 — HCI Connection

**PatientZero is an HCI research tool**

The interaction under study: simulated patient ↔ AI doctor

- Vary explanation design systematically across populations
- Measure comprehension effects at scale before human studies
- Identify which populations are most affected by which design choices
- Iterate on interaction design with a tight feedback loop

Instead of recruiting for every cell in the condition matrix, simulate
first — then validate the cells that matter with real participants.

---

## Slide 13 — Limitations & Future Work

**Limitations**
- LLM-simulated patients not validated against real patient behavior
- LLM-as-judge — no human ground truth on evaluation scores
- Distributions are US-centric (NAAL, Census, NHIS data)
- Single feedback loop strategy (failure-case-driven)

**Future work**
- Human validation study: do simulated patients behave like real ones?
- Domains beyond medicine (financial literacy, legal, education)
- DSPy-based optimizer for the feedback loop
- Community-contributed distributions for non-US populations

---

## Slide 14 — Contributions

- **Open-source framework** — `pip install patientzero`, domain-generic
- **Causal demographic distributions** grounded in real clinical and survey data
- **Reproducible experiments** with seeded sampling and coverage tracking
- **Automated prompt optimization** via versioned feedback loop
- **Applied to medical communication** — measurable comprehension gains for low-literacy populations across five evaluation dimensions

---

## Slide 15 — Questions

Surya Mani · Aaron Tamte · Lile Zhang
CS6170 — Spring 2026
