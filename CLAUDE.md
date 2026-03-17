# CLAUDE.md

## Project: PatientZero

Research simulation system studying how AI explanation styles (clinical vs analogy) and interaction modes (static vs dialog) affect patient comprehension of medical information.

## Repo Layout

This is a git submodule inside the parent `AI_Capstone` repo.

```
project/
├── core/          # Pure Python logic (agents, llm, config, db, simulation, types)
├── backend/       # Thin FastAPI HTTP layer + tests
├── evaluations/   # Evaluation scripts (import core directly, no server needed)
├── frontend/      # React + Vite + TypeScript app
├── plan/          # Implementation plans
├── pyproject.toml # Python deps (uv), at project root
└── report.txt     # Research report
```

## Working Directory

**All commands run from project root** (`project/`), not `backend/`.

- **Install deps**: `uv sync`
- **Run server**: `uv run uvicorn backend.api.main:app --reload`
- **Run tests**: `uv run python -m pytest backend/tests/ -v`
- **Run evaluations**: `uv run python -m evaluations.simulate.test_simulate`

## Core (`core/`)

All domain logic lives here. No FastAPI dependency.

```
core/
├── types/         # Dataclasses: Persona, Scenario, Message, AgentStep, AgentTrace, SimulationState
├── agents/        # Agent base class + PatientAgent, ExplainerAgent, JudgeAgent, prompts/
├── llm/           # LLMProvider ABC, factory, MockProvider, OpenAIProvider
├── config/        # Settings, personas
├── db/            # Database class, schema, queries
└── simulation/    # Simulation orchestrator with state machine (run/step/pause/resume/stop)
```

### Types (`core/types/`)

- `Persona` — 8-field dataclass (name, age, education, literacy_level, anxiety, prior_knowledge, communication_style, backstory)
- `Scenario` — 4-field dataclass (test_name, results, normal_range, significance)
- `Message` — role + content
- `AgentStep` — single LLM call record (agent_type, model, system_prompt, input/output, timing, error)
- `AgentTrace` — full trajectory of steps with `add()`, timing, `transcript`, `to_dict()`
- `SimulationState` — enum: IDLE, RUNNING, PAUSED, COMPLETED, ERROR

### LLM Provider Architecture

Factory pattern with abstract base class:

- `core/llm/base.py` — `LLMProvider` ABC with `async stream()` method
- `core/llm/factory.py` — `get_provider()` singleton factory + `parse_provider_model()` parser
- `core/llm/mock.py` — `MockProvider` for testing (configurable delay)
- `core/llm/openai_provider.py` — `OpenAIProvider` wrapping `AsyncOpenAI`, used for any OpenAI-compatible API

**Models use `"provider:model"` string format** (e.g., `"kimi:kimi-k2.5"`). Parsed by `parse_provider_model()`.

**Current providers**: `mock`, `kimi` (Moonshot API via OpenAI-compatible client). `claude` and `local` are listed in AVAILABLE_MODELS but not yet implemented.

### Adding a new LLM provider

1. Create `core/llm/<name>.py` implementing `LLMProvider.stream()`
2. Add a `case` in `core/llm/factory.py:get_provider()`
3. Add model strings to `core/config/settings.py:AVAILABLE_MODELS`
4. Add env vars to `.env.example`

### Agents (`core/agents/`)

Three agent types built on `core/agents/base.py`:
- **PatientAgent** — simulates patients with `Persona` dataclass
- **ExplainerAgent** — explains medical test results with `Scenario` dataclass (4 prompt variants)
- **JudgeAgent** — evaluates patient comprehension, returns JSON

`Agent.respond()` returns `AgentStep`. `Agent.stream()` yields tokens.

### Simulation (`core/simulation/`)

`Simulation` class orchestrates explainer/patient conversations with state machine:
- `run()` — runs all turns, returns `AgentTrace`
- `step()` — executes one turn, pauses
- `pause()` / `resume()` / `stop()` — state control
- `run_streaming()` — yields `(event_type, data)` tuples for SSE

### API

All endpoints prefixed with `/api`. Chat uses SSE streaming. Sessions store model selection. Backend routes in `backend/api/routes/`.

## Frontend

- React + Vite + TypeScript
- Tailwind CSS + shadcn/ui components
- `cd frontend && npm install && npm run dev` to run (port 5173)

## Environment

Config via `.env` file at project root (see `.env.example`). Key vars:
- `KIMI_API_KEY` — for Moonshot/Kimi provider
- `ANTHROPIC_API_KEY` — for Claude provider (not yet implemented)
- `LLM_PROVIDER` — active default provider (`mock` by default)

## Evaluations

Evaluation scripts in `evaluations/` that import `core` directly — no running server needed.

```
evaluations/
├── __init__.py
└── simulate/
    ├── __init__.py
    └── test_simulate.py
```

## Testing

71 tests covering agents, API routes, DB queries, LLM factory, and simulation runner. All use `MockProvider(delay=0)`. Test fixtures in `backend/tests/conftest.py`.
