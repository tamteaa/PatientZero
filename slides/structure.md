# Slide Structure

What each slide needs to accomplish in the talk. Audience is HCI
students and faculty (CS6170). They care about the research problem,
the method, ecological validity, and findings — not implementation
details.

## Slide 1 — Title

Frame PatientZero as a research contribution to HCI, not a software
product. The audience should understand this is about studying
human-AI medical communication through simulation.

## Slide 2 — The Problem

Establish the real-world stakes. AI is already how people get health
information, and most people can't understand what they're told. This
is measured, not hypothetical. The audience should feel the gap between
how AI delivers medical information and how patients actually process it.

## Slide 3 — Why Simulation

Real patient studies are the gold standard but they don't scale. You
get 12-16 participants, one population slice, and no ability to rerun
after changing the intervention. Simulation lets you explore the full
demographic space before committing to expensive human validation. The
audience should see simulation as a methodological tool, not a shortcut.

## Slide 4 — No Good Methods Exist

This is the gap. Existing LLM simulation work samples traits
independently (producing unrealistic combinations), has no systematic
evaluation, no coverage tracking, no reproducibility, and no way to
improve prompts except by hand. The audience should understand that
realistic patient simulation is an unsolved problem, and that's what
motivated the project.

## Slide 5 — The Pivot

Show the shift from human participant study to framework. The original
proposal assumed simulation was a solved tool you could use as a
validation step. It isn't. The realization: building the method itself
is the contribution.

## Slide 6 — PatientZero: What We Built

Introduce the three core concepts at a research level:
- Agent: a simulated participant with a demographic profile drawn from
  a causal trait distribution
- Judge: a structured multi-dimensional evaluator for conversations
- Experiment: a reproducible container that runs simulations, tracks
  coverage, and optimizes prompts automatically

No code. No API. The audience should understand the conceptual design
of the framework and why each piece exists.

## Slide 7 — Causal Distributions

The key methodological contribution. This is what makes simulated
patients ecologically valid rather than random. Show the trait DAGs
and explain that traits are correlated because real populations are
correlated. Name the data sources (NAAL, NHIS, Census, RIAS, CAHPS).
The audience should understand this as a validity argument: these
aren't made-up personas, they're sampled from real clinical and
demographic data.

## Slide 8 — System Architecture

How the pieces connect end-to-end. High-level flow: sample profiles
from distributions → run multi-turn conversation between doctor and
patient agents → judge evaluates the transcript on multiple dimensions
→ coverage analysis identifies which populations were tested →
feedback loop proposes improved prompts → repeat. Keep it conceptual.

## Slide 9 — Evaluation

What the judge measures and why those dimensions matter for medical
communication. Comprehension, factual recall, applied reasoning,
explanation quality, interaction quality. These aren't arbitrary —
they're grounded in what health communication research says matters
for patient outcomes. The audience should see these as validated
constructs, not random metrics.

## Slide 10 — The Feedback Loop

How prompts improve automatically. The system identifies the
worst-performing conversations, analyzes what went wrong, proposes
new prompt templates, and measures whether they actually help. Targets
are versioned so every generation's results are preserved and
comparable. The audience should see this as closing the design loop:
measure → diagnose → intervene → re-measure.

## Slide 11 — Results

Show that the framework produces real, interpretable findings.
Baseline vs optimized prompts across all five dimensions. The feedback
loop found that low-literacy patients needed more comprehension checks
and the optimized prompt measurably improved scores. The audience
should leave believing the framework can generate actionable insights
about medical communication.

## Slide 12 — HCI Connection

Connect back to CS6170. PatientZero is an HCI research tool. The
interaction under study is a simulated human interacting with an AI
doctor. The framework lets researchers vary explanation design
systematically across populations, measure effects at scale, and
identify which populations are most affected — before running
expensive human studies. The framework makes the experimental
condition matrix tractable.

## Slide 13 — Limitations & Future Work

Be honest about what's not done and what that means for the claims.
LLM patients aren't validated against real patients — the distributions
are grounded in real data but the simulated behavior itself is unproven.
Judge is LLM-based with no human ground truth. Distributions are
US-centric. Future work: human validation study, broader domains,
improved optimizer.

## Slide 14 — Contributions

The takeaway list. Open-source framework (pip install patientzero),
causal distributions from real data, reproducible experiments with
coverage tracking, automated prompt optimization, applied to medical
communication with measurable results. The release as a pip package
goes here — it's a contribution, not a framing device.

## Slide 15 — Questions

Close.
