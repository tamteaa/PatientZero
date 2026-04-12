# PatientZero

[![CI](https://github.com/tamteaa/PatientZero/actions/workflows/ci.yml/badge.svg)](https://github.com/tamteaa/PatientZero/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/patientzero)](https://pypi.org/project/patientzero/)
[![Python](https://img.shields.io/pypi/pyversions/patientzero)](https://pypi.org/project/patientzero/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A simulation framework that uses LLM-powered agents to model doctor-patient interactions around medical test results and evaluate patient comprehension. A **DoctorAgent** explains, a **PatientAgent** responds, and a **JudgeAgent** scores comprehension.

## Install

```bash
pip install patientzero            # core + OpenAI provider
pip install patientzero[backend]   # + FastAPI backend
```

Requires Python 3.11+.

## Quick start

```python
import asyncio
from patientzero import Agent, Distribution, Experiment, ExperimentConfig, JudgeConfig

exp = Experiment(ExperimentConfig(
    name="demo",
    agents=(
        Agent(
            "doctor",
            "You are a doctor explaining test results. Be {empathy}.",
            Distribution(empathy={"empathetic": 0.5, "clinical": 0.5}),
        ),
        Agent(
            "patient",
            "You are a patient with {literacy} health literacy.",
            Distribution(literacy={"low": 0.5, "high": 0.5}),
        ),
    ),
    judge=JudgeConfig(
        rubric={"clarity": "How clear was the explanation?"},
        instructions="Evaluate the interaction.",
        model=None,
    ),
    model="openai:gpt-4o",  # or "mock:default" for testing
))

async def main():
    await exp.run(n=5)
    print(exp.scores())

asyncio.run(main())
```

To persist results to disk:

```python
from patientzero.db.database import Database

db = Database("experiments.db")
db.init()
exp = Experiment(config, db=db)
```

## Development setup

```bash
git clone https://github.com/tamteaa/PatientZero.git
cd PatientZero
cp .env.example .env       # configure API keys
uv sync --extra dev --extra backend
```

**Run the backend:**
```bash
uv run uvicorn backend.api.main:app --reload
```

**Run the frontend:**
```bash
cd frontend && npm install && npm run dev
```

Open http://localhost:5173.

**Run tests:**
```bash
uv run python -m pytest patientzero/tests/ backend/tests/ -v
```

## LLM providers

Models use `"provider:model"` format:

| Provider | Example | Notes |
|----------|---------|-------|
| `mock` | `mock:default` | Deterministic responses for testing |
| `openai` | `openai:gpt-4o` | Requires `OPENAI_API_KEY` |
| `kimi` | `kimi:kimi-k2.5` | Requires `KIMI_API_KEY` |
| `claude` | `claude:claude-sonnet-4-20250514` | Via Claude CLI |
| `local` | `local:llama3` | Any OpenAI-compatible local server |

## CI/CD

- **CI** runs on every push and PR: tests across Ubuntu, macOS, and Windows on Python 3.11, 3.12, and 3.13.
- **Publish** triggers on GitHub release creation, pushing to PyPI via trusted publishing.

## Authors

Surya Mani, Aaron Tamte, Lile Zhang

## License

[MIT](LICENSE)
