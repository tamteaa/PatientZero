# PatientZero — Implementation Plan

## Component Status

| Component | Status | Notes |
|-----------|--------|-------|
| Profile Generator | Done | Static generators wired to /personas/generate and /doctors/generate |
| Scenario Generator | Done | Static + LLM generators, wired to /scenarios/generate |
| Simulation Engine | Done | Full state machine, streaming, pause/resume/stop |
| Evaluation Layer | Done | 5 dimensions + confidence-comprehension gap, 10 test cases, cached |
| Analysis | Done | Aggregation by patient/doctor traits + scenario, worst combinations, CSV export |
| Feedback Loop | Not started | Depends on analysis |

---

## 1. Profile Generators

### Goal
Generate realistic patient and doctor profiles at scale, so that the distribution of simulated interactions reflects who actually shows up in clinical settings.

### Patient Profiles — Real Data Sources

**Health literacy distributions:**
- NAAL (National Assessment of Adult Literacy) — ~36% of US adults have basic or below-basic health literacy. Breaks down by age, education, race/ethnicity.
- S-TOFHLA / REALM scores — validated instruments that map health literacy to demographic variables. Published norms give us the joint distribution of literacy × age × education.

**Demographics:**
- Census / ACS data — age, education level, primary language distributions for the US population (or target population).
- NHIS (National Health Interview Survey) — health anxiety prevalence, chronic condition rates by demographic.

**Behavioral tendencies:**
- Health psychology literature — documented patterns like "agreement bias" (nodding along when confused) correlating with low literacy, or "information avoidance" correlating with high anxiety.
- These map to the `tendency` trait in AgentProfile.

### Patient Profile Generator — How It Works

**Static generator:**
1. Define marginal distributions for each trait from the data sources above (e.g., literacy: 36% low, 40% moderate, 24% high per NAAL).
2. Define correlations between traits (low education correlates with low literacy, older age correlates with higher anxiety about results).
3. Sample profiles by drawing from the joint distribution — not independently per trait, since traits are correlated.
4. Map sampled numeric values to descriptive trait strings that go into the prompt (e.g., literacy score 2/5 → "low", anxiety percentile 85 → "high").

**LLM generator:**
- Provide the LLM with population-level statistics and ask it to generate a diverse set of profiles that match the overall distribution.
- Useful for generating realistic backstories and behavioral nuance that pure statistical sampling can't capture.

**Validation of distributions:**
- After generating N profiles, compute the empirical distribution of each trait and compare against the target distribution (chi-squared test or KL divergence).
- Flag if any trait is over/under-represented beyond a threshold.
- For the LLM generator, include distribution targets in the prompt and verify the output matches.

### Doctor Profiles — Real Data Sources

Doctor communication style is less neatly quantified than patient demographics, but there is data:

**Communication patterns:**
- CAHPS (Consumer Assessment of Healthcare Providers) — patient-reported measures of doctor communication (listened carefully, explained things clearly, spent enough time). Published distributions by specialty and setting.
- Roter Interaction Analysis System (RIAS) — coded categories of doctor communication behavior in real clinical encounters. Gives frequency distributions of informing, questioning, emotional responsiveness.

**Relevant traits to model:**
- Empathy level (correlates with patient satisfaction and comprehension outcomes)
- Verbosity / explanation thoroughness (some doctors give detailed explanations, others are terse)
- Comprehension checking behavior (do they ask "does that make sense?" or just move on)
- Time pressure (high-volume settings → rushed explanations)

**Static generator:** Sample from RIAS-derived distributions of communication behaviors, map to trait strings.

**LLM generator:** Generate doctor profiles with realistic backstories and practice settings that imply communication styles.

---

## 2. Analysis Layer

### Goal
Aggregate evaluation scores across many simulation runs to identify systematic patterns in where doctor communication fails.

### Key Questions the Analysis Must Answer
1. **Which patient types are left behind?** — Break down comprehension scores by literacy, anxiety, age, education. Is there a literacy threshold below which comprehension drops sharply?
2. **Which concepts consistently confuse?** — Break down by scenario type. Are medication instructions harder to convey than lab results? Do multi-abnormality scenarios cause more confusion?
3. **Which doctor behaviors cause failures?** — Break down by doctor traits. Do terse doctors produce worse comprehension? Does high empathy compensate for low literacy?
4. **Where are comprehension checks missing?** — Use interaction quality scores to identify when doctors fail to verify understanding. Correlate with confidence-comprehension gaps.
5. **Which combinations are worst?** — Cross patient traits × doctor traits × scenario type. Find the specific failure modes (e.g., terse doctor + low-literacy patient + medication scenario).

### Implementation
- Run batch simulations across generated profiles × scenarios (N doctors × M patients × K scenarios)
- Collect all evaluation scores into a structured dataset
- Compute: means, standard deviations, effect sizes (Cohen's d) per trait grouping
- Statistical tests: ANOVA across trait levels, interaction effects
- Export to CSV/JSON for external analysis (R, Python notebooks)
- Optionally: summary report generation (top-N failure modes, most impactful traits)

### Validation
- Compare simulation-derived patterns against published clinical findings. For example:
  - If NAAL data shows low-literacy patients have 3x higher medication error rates, do our simulated low-literacy patients show correspondingly lower comprehension scores on medication scenarios?
  - If CAHPS data shows empathetic doctors get higher patient satisfaction, do our high-empathy doctor agents produce higher interaction quality scores?
- Discrepancies between simulation findings and published clinical findings indicate either generator miscalibration or judge scoring bias — both of which feed into the feedback loop.

---

## 3. Feedback Loop

### Goal
Use analysis findings to iteratively improve doctor agent communication, and re-validate that identified gaps close.

### How It Works
1. **Identify failures** — Analysis surfaces specific failure modes (e.g., "Doctor agents with low empathy + terse verbosity produce comprehension scores below 30 for low-literacy patients on medication scenarios").
2. **Diagnose cause** — Review turn-by-turn logs for failing simulations. Is the doctor using too much jargon? Skipping comprehension checks? Moving too fast?
3. **Refine doctor behavior** — Modify doctor prompts or profile traits to address the gap. This could be:
   - Adding instructions to the doctor prompt (e.g., "always check understanding after explaining dosing")
   - Adjusting trait distributions (e.g., increasing baseline empathy)
   - Adding scenario-specific instructions (e.g., "for medication scenarios, explain side effects using concrete examples")
4. **Re-run** — Run the same profile × scenario combinations with the refined doctor agents.
5. **Measure gap closure** — Compare before/after scores. Did comprehension improve? Did the gap between high-literacy and low-literacy patients narrow?
6. **Iterate** — If gaps remain, diagnose further and refine again.

### What This Produces
A set of evidence-based recommendations for doctor communication: "When explaining medication instructions to patients with low health literacy, the following behaviors significantly improve comprehension: [list]." Backed by simulation data showing the before/after effect sizes.

---

## Order of Operations
1. **Profile generators** — unblocks running at scale with realistic distributions
2. **Analysis** — unblocks identifying patterns across runs
3. **Feedback loop** — uses analysis output to iterate on doctor behavior
