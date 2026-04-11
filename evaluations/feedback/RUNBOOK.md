# Feedback Loop Runbook

## Two paths (synthesized)

1. **Product / DB experiments** — Create an experiment via `POST /api/experiments` (UUID). Every simulation **must** reference that UUID as `experiment_id`. The runner uses the experiment’s frozen patient/doctor distributions. The sim **also** loads prompts from that experiment’s **current `OptimizationTarget`** (same templates as `prompts.py` until Optimize changes them).
2. **Manual batch labels** — Pass optional `batch_id` on `POST /api/simulate` or `--batch-id` on the CLI runner. This string is stored in `config_json` and used by **`/api/analysis/compare`** (query params are still named `baseline_experiment_id` / `candidate_experiment_id` but values match **`batch_id`**).

## Metadata convention

- **`experiments.id` (UUID)** — DB container; required for every simulation.
- **`batch_id`** (optional string) — Feedback-batch label (e.g. `baseline_low_lit_v2_n10_restart`) for compare/export. Legacy runs may still have `experiment_id` inside `config_json`; analysis accepts either key.
- **`policy_version`** — Doctor behavior variant (`baseline`, `v2_low_literacy_checks`, …) appended on top of the target’s doctor template.
- **`style`** — Explanation style (`clinical`, `empathetic`, `analogy`, `simplified`).

## Guardrails

- Stage run sizes: 10 → 20 → 40; cap `n-runs` at 100.
- Use a **fresh `batch_id` per batch** so exports stay clean.
- Same simulation + judge model per A/B pair.
- Prefer **`--sim-timeout-s 300`** for Kimi to reduce stalls.

## Create a DB experiment (once)

```bash
curl -s -X POST http://localhost:8000/api/experiments -H "Content-Type: application/json" \
  -d '{"name":"Feedback loop main"}' | jq -r .id
```

Use the returned UUID as `--experiment-db-id` below.

## Baseline batch (CLI)

```bash
uv run python -m evaluations.feedback.run_feedback_cycle \
  --experiment-db-id "<UUID_FROM_POST_EXPERIMENTS>" \
  --batch-id baseline_v1 \
  --policy-version baseline \
  --model kimi:kimi-k2.5 \
  --judge-model kimi:kimi-k2.5 \
  --n-runs 10 \
  --max-turns 8 \
  --sim-timeout-s 300
```

## Intervention batch

```bash
uv run python -m evaluations.feedback.run_feedback_cycle \
  --experiment-db-id "<UUID_FROM_POST_EXPERIMENTS>" \
  --batch-id intervention_v2 \
  --policy-version v2_low_literacy_checks \
  --model kimi:kimi-k2.5 \
  --judge-model kimi:kimi-k2.5 \
  --n-runs 10 \
  --max-turns 8 \
  --sim-timeout-s 300
```

(`--experiment-id` is accepted as a deprecated alias for `--batch-id`.)

## Compare two batches

Values must match the **`batch_id`** strings you used (legacy: old `config_json.experiment_id`).

```bash
curl "http://localhost:8000/api/analysis/compare?baseline_experiment_id=baseline_v1&candidate_experiment_id=intervention_v2"
```

## HTTP simulate (same experiment + optional batch)

```json
{
  "experiment_id": "<UUID>",
  "model": "mock:default",
  "batch_id": "optional_batch_label",
  "style": "clinical",
  "policy_version": "baseline"
}
```

## Artifacts

Each CLI run writes under `evaluations/feedback/artifacts/<batch_id>/`:

- `analysis.json`, `analysis.csv`, `analysis_experiment.csv`, `run_summary.json`

## See also

- `evaluations/feedback/RECOMMENDATIONS.md` — evidence summary (low-literacy A/B).
- `todos.md` — OptimizationTarget + DSPy roadmap and blocker notes.
