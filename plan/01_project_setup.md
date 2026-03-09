# Phase 1: Project Setup & Config

## Tasks

### 1.1 Initialize Python project
- Use `uv` for dependency management
- Python 3.12+
- Set up `pyproject.toml` with dependencies

### 1.2 Dependencies
```
anthropic          # Claude API (or openai for GPT)
pydantic           # Data models & validation
scipy              # Statistical tests (ANOVA, Kruskal-Wallis)
numpy              # Numerical computation
pandas             # Data manipulation
matplotlib         # Plotting
seaborn            # Statistical visualization
pingouin           # ANOVA, effect sizes, ICC
bootstrapped       # Bootstrap confidence intervals
```

### 1.3 Configuration
- `config/settings.py`: API keys (via env vars), model selection, temperature settings, max tokens
- `config/conditions.py`: Define the 2×2 conditions as an enum or dataclass

```python
# Conditions
class ExplanationStyle(Enum):
    CLINICAL = "clinical_direct"
    ANALOGY = "analogy_enriched"

class InteractionMode(Enum):
    STATIC = "static_reading"
    DIALOG = "interactive_dialog"

@dataclass
class Condition:
    style: ExplanationStyle
    mode: InteractionMode
```

### 1.4 Data models (Pydantic)
- `Session`: persona_id, condition, scenario, transcript, scores
- `Turn`: role, content, timestamp
- `Score`: comprehension, explanation_quality, interaction_quality, confidence, satisfaction
- `Persona`: id, literacy_level, anxiety, prior_knowledge, communication_style, demographics

### 1.5 Decision: Which LLM?
- Claude (Anthropic API) recommended — good at following complex persona prompts
- Need to decide: same model for all agents, or different models?
- Recommendation: same model (e.g., Claude Sonnet) for Explainer & Patient, potentially a stronger model (Claude Opus) for Judge
