# Distributions & Sampling

Simulations need two inputs: **who** (agent profiles) and **what**
(the scenario). Both come from distributions declared on each `Agent`.

## How Sampling Works

Each `Agent` owns a `Distribution` — a DAG of discrete trait nodes.
Traits are either unconditioned (`Marginal`) or depend on a parent
trait (`Conditional`). The DAG is topo-sorted at construction and
sampled in causal order.

```
  Patient Distribution                  Doctor Distribution

  age ──────┬──▶ literacy               setting ──▶ time_pressure ──▶ verbosity
            │
            └──▶ anxiety                empathy ──▶ comprehension_checking
```

This keeps profiles realistic: a low-literacy patient is more likely
to be older; a rushed doctor is more likely to be in the ER.

## Defining a Distribution

```python
from core.distribution import Distribution, Conditional

US_ADULT_PATIENT = Distribution(
    age={"young": 0.35, "middle": 0.40, "elderly": 0.25},
    education=Conditional("age", {
        "young":   {"high_school": 0.3, "college": 0.5, "graduate": 0.2},
        "middle":  {"high_school": 0.4, "college": 0.4, "graduate": 0.2},
        "elderly": {"high_school": 0.6, "college": 0.3, "graduate": 0.1},
    }),
    literacy=Conditional("education", {
        "high_school": {"low": 0.5, "medium": 0.4, "high": 0.1},
        "college":     {"low": 0.1, "medium": 0.5, "high": 0.4},
        "graduate":    {"low": 0.05, "medium": 0.25, "high": 0.7},
    }),
    anxiety=Conditional("age", {
        "young":   {"calm": 0.6, "moderate": 0.3, "anxious": 0.1},
        "middle":  {"calm": 0.4, "moderate": 0.4, "anxious": 0.2},
        "elderly": {"calm": 0.3, "moderate": 0.3, "anxious": 0.4},
    }),
)
```

## Sampling with Constraints

```python
rng = random.Random(42)

# unconstrained — full causal chain
profile = dist.sample(rng)
# {'age': 'elderly', 'education': 'high_school', 'literacy': 'low', 'anxiety': 'anxious'}

# pinned — force literacy, rest samples normally
profile = dist.sample(rng, literacy="low")
# {'age': 'young', 'education': 'college', 'literacy': 'low', 'anxiety': 'calm'}
```

Constraints are how the API's `where` filter works — e.g. "only run
anxious patients" without producing impossible trait combinations.

## Introspection

```python
dist.traits          # ('age', 'education', 'literacy', 'anxiety')
dist.topo_order      # same, but guaranteed causal order
dist.support         # {'age': ['young', ...], 'literacy': ['low', ...], ...}
dist.marginal('literacy')   # P(literacy) with ancestors integrated out
dist.cells('age', 'literacy')  # exact joint: [((young, low), 0.06), ...]
```

## Mutation (Returns New Distribution)

```python
# replace one node
new_dist = dist.replace("anxiety", {"calm": 0.5, "anxious": 0.5})

# reweight a marginal (severs parent dependency)
new_dist = dist.reweight("age", {"young": 0.5, "elderly": 0.5})
```

## Reproducibility

Experiments control reproducibility via `stable_rng(seed, draw_index)`
from `core/sampling.py`. Each simulation gets its own deterministic RNG
derived from the experiment seed + a monotonic counter. If you add
sampling logic, thread the `rng` parameter — one stray `random.random()`
call breaks reproducibility for the whole chain.

## Data Sources

The example medical distributions (`core/examples/medical/distributions.py`)
are grounded in real survey data:

- **Patient**: NAAL (literacy|education), NHIS (anxiety|age), US Census
- **Doctor**: RIAS, CAHPS (physician communication patterns)
