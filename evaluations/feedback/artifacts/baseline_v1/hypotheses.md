# Baseline v1 Failure Modes and Hypotheses

## Dataset Scope

- Experiment ID: `baseline_v1`
- Completed + evaluated runs: 3
- Model: `kimi:kimi-k2.5`
- Policy version: `baseline`

## Observed Failure Modes

1. **Low-literacy patients underperform even with empathetic or thorough doctors**
   - Two low-literacy runs scored 50 and 55 comprehension.
   - Both runs show explicit confidence-comprehension gaps.
2. **Factual recall collapses first**
   - Low-literacy runs showed factual recall of 15 and 25 despite moderate interaction quality.
3. **Over-verbose explanations can still fail**
   - One low-literacy case used `doctor_verbosity=thorough` but still scored 55 with a gap.

## Ranked Intervention Hypotheses

1. **H1 (Highest Priority): Mandatory teach-back loop for low-literacy interactions**
   - Add a required mini teach-back after each key medical concept.
   - If patient response is incomplete/incorrect, rephrase in plain language before advancing.
   - Expected effect: increase comprehension and factual recall for low-literacy cohort, reduce gap rate.

2. **H2: Chunking and simplification constraints**
   - Force 2-4 short paragraphs per response and one action-oriented summary sentence.
   - Expected effect: reduce overload and improve recall in low/moderate literacy segments.

3. **H3: Anxiety-aware framing**
   - Start with reassurance + concern acknowledgment before numbers/terminology.
   - Expected effect: improve interaction quality and reduce false-confidence responses.

## Intervention Selected for Iteration 1

- **Selected hypothesis:** H1
- **Policy version:** `v2_low_literacy_checks`
- **Rationale:** strongest direct alignment with observed failure pattern (confidence-comprehension gaps in low-literacy cases).
