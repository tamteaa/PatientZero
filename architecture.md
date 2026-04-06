# PatientZero Architecture

## Purpose

A simulation framework for identifying gaps in doctor-patient communication at scale. Generators produce realistic patient profiles and medical scenarios — initialized from real clinical/demographic data or population defaults — and the system runs thousands of simulated conversations to surface where doctor explanations fail specific patient populations.

## System Overview

```
                    Real Data (optional)
                    - Demographics / health literacy surveys
                    - Clinical test prevalence & distributions
                    - Physician communication patterns
                            |
                            v
  +-------------------+       +---------------------+
  | Profile Generator |       | Scenario Generator  |
  |                   |       |                     |
  | From real data:   |       | From real data:     |
  |   demographics,   |       |   clinical test     |
  |   literacy dist.  |       |   distributions,    |
  |                   |       |   prevalence rates  |
  | Or defaults:      |       |                     |
  |   general pop.    |       | Or defaults:        |
  |   distributions   |       |   reference ranges  |
  +--------+----------+       +---------+-----------+
           |                            |
           v                            v
  +------------------------------------------------+
  |              Simulation Engine                  |
  |                                                |
  |  Independent Variables:                        |
  |    Patient — literacy, anxiety, age, tendency  |
  |    Doctor  — empathy, verbosity, style         |
  |    Scenario — complexity, test type, severity  |
  |                                                |
  |  DoctorAgent  <----turn---->  PatientAgent     |
  |                                                |
  |  Output: conversation transcript               |
  +------------------------+-----------------------+
                           |
                           v
  +------------------------------------------------+
  |              Evaluation Layer                   |
  |                                                |
  |  Dependent Variables (per transcript):         |
  |    - Patient comprehension                     |
  |    - Factual recall                            |
  |    - Applied reasoning                         |
  |    - Explanation quality                       |
  |    - Interaction quality                       |
  |    - Confidence-comprehension gaps             |
  +------------------------+-----------------------+
                           |
                           v
  +------------------------------------------------+
  |                Analysis                         |
  |                                                |
  |  Aggregate across runs to identify:            |
  |    - Which patient types are left behind?      |
  |    - Which concepts consistently confuse?      |
  |    - Where are comprehension checks missing?   |
  |    - Which doctor behaviors cause failures?    |
  +------------------------+-----------------------+
                           |
                           | identified gaps
                           v
  +------------------------------------------------+
  |              Feedback Loop                      |
  |                                                |
  |  Refine doctor agent behavior based on         |
  |  identified communication failures:            |
  |    - Adjust prompts / profiles                 |
  |    - Re-run simulations                        |
  |    - Measure whether gaps close                |
  +------------------------------------------------+
```

## Research Value

The framework scales identification of doctor communication failures beyond what is possible with real patients. Real clinical and demographic data feeds the generators to ensure realistic inputs. The system then systematically varies patient profiles, doctor behaviors, and scenario complexity to discover which combinations produce comprehension failures — and iterates on the doctor side to close those gaps.
