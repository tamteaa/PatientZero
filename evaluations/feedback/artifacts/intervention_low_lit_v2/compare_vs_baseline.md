# Low-literacy cohort: `baseline_low_lit_v1` vs `intervention_low_lit_v2`

## Protocol

- Both batches: `patient_literacy=low`, `n_runs=3`, `max_turns=2`, model/judge `kimi:kimi-k2.5`, style `clinical`.
- Baseline policy: `baseline`.
- Intervention policy: `v2_low_literacy_checks`.

## Data caveat

`analysis_experiment.csv` for `intervention_low_lit_v2` lists **6** rows because a prior attempt used the same `experiment_id`. **Primary comparison** uses the **3 newest** evaluations (first 3 data rows; consistent with `run_summary.json` `n_evaluated: 3` from the latest run).

## Primary deltas (candidate - baseline), n=3 vs n=3

| Metric | Baseline mean | Intervention mean | Delta |
|--------|----------------|-------------------|-------|
| Comprehension | 67.67 | 81.67 | **+14.0** |
| Factual recall | 40.67 | 66.67 | **+26.0** |
| Applied reasoning | 57.67 | 80.00 | **+22.33** |
| Explanation quality | 60.67 | 82.00 | **+21.33** |
| Interaction quality | 59.33 | 85.67 | **+26.34** |

- Confidence-comprehension **gap rate**: 66.7% -> 33.3% (**-33.3 pp**).

## Closure (plan-aligned)

- **Target cohort lift**: comprehension and secondary metrics improved on the matched n=3 slice.
- **Gap reduction**: large reduction in gap rate on the same slice.
- **Non-target regression**: not evaluated here (slice is low-literacy only).

## Next steps

- Use a **fresh `experiment_id` per batch** (or DB hygiene) so artifact CSVs stay one-batch clean.
- Increase **N** (e.g. 20-40) and **max_turns** (e.g. 6-8) for stable estimates; repeat compare via `/api/analysis/compare` or this artifact pattern.
