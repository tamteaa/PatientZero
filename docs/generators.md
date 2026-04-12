# Generators

Generators produce the two inputs a simulation needs: the **scenario** (what the doctor is explaining) and the **profiles** (who the doctor and patient are). They live in `core/generators/` and are pure producers — no DB, no agents, no experiment awareness.

## Scenarios

Two flavors:

- **Static** — samples from six hardcoded test panels (CBC, BMP, Lipid, Thyroid, HbA1c, Liver). Each panel has reference ranges and per-component clinical significance strings; an `abnormal_ratio` knob controls how often values fall outside normal. Use this in tests and offline runs.
- **LLM** — prompts any `LLMProvider` for a JSON array of scenarios. Use when you want variety the static panels can't cover.

The static generator is the default because it's fast, deterministic, and doesn't need API keys.

## Profiles

Patient and doctor profiles are **correlated**, not independent — traits are drawn through a causal chain so the combinations stay realistic. A low-literacy patient is more likely to be older and less educated; a rushed doctor is more likely to be in an ER setting.

The chains are grounded in real survey data:

- **Patient**: NAAL (literacy given education), NHIS (anxiety given age), US Census (demographic groups for names).
- **Doctor**: RIAS and CAHPS (physician communication distributions).

Traits can be pinned at call time — e.g. force `literacy="low"` and the rest of the chain still samples conditionally on that. This is how UI filters like "only anxious patients" work without producing nonsense combinations.

## Reproducibility

Every generator accepts an optional `random.Random`. The experiment runner hands one in per sample, seeded from the experiment's `sampling_seed`, so re-running an experiment produces the same sequence of scenarios and profiles. If you add a generator, thread the RNG through every random call — one stray `random.random()` breaks reproducibility for the whole chain.
