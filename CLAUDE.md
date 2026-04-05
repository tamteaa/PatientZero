# CLAUDE.md

## Project: PatientZero

Simulation system that uses LLM agents to simulate doctor-patient interactions around medical test results. A DoctorAgent explains, a PatientAgent responds, and a JudgeAgent scores comprehension.

## Commands

All commands run from project root (`project/`), not `backend/`.

```bash
uv sync                                              # install python deps
uv run uvicorn backend.api.main:app --reload          # run backend
uv run python -m pytest backend/tests/ -v             # run tests
uv run python -m evaluations.judge.run [--model M]    # run judge evals
cd frontend && npm install && npm run dev              # run frontend (port 5173)
```

## Repo Structure

```
core/           # All domain logic, no FastAPI dependency
  agents/       # DoctorAgent, PatientAgent, JudgeAgent + prompts.py
  llm/          # LLMProvider ABC, factory, Mock/OpenAI/ClaudeCLI providers
  services/     # run_simulation_streaming() orchestration
  simulation/   # Simulation runner (state machine: run/step/pause/resume/stop)
  config/       # Settings, personas, 3 scenarios (CBC, HbA1c, Metformin)
  db/           # SQLite (WAL), schema.sql, queries/{sessions,simulations,evaluations}.py
  types/        # Dataclasses & enums split across modules, re-exported from __init__
backend/        # FastAPI routes (chat.py, simulate.py), tests
evaluations/    # Judge eval harness — hardcoded transcripts, auto-discovered
frontend/       # React 19 + Vite + TS, Tailwind + shadcn/ui
```

## Key Patterns

- **LLM models** use `"provider:model"` format (e.g. `"kimi:kimi-k2.5"`). Parsed by `parse_provider_model()` in `core/llm/factory.py`.
- **Providers**: `mock` (testing), `kimi`, `claude` (via CLI), `openai`, `local`. Factory in `core/llm/factory.py`.
- **Prompts** are format-string templates in `core/agents/prompts.py` (not a directory).
- **Simulation** alternates doctor/patient turns via SSE streaming. Service layer in `core/services/simulation.py` handles DB persistence.
- **API** endpoints all prefixed with `/api`. Routes in `backend/api/routes/`.
- **Environment**: `.env` at project root. Key vars: `LLM_PROVIDER` (default `mock`), `KIMI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`. See `.env.example`.

## Testing

Tests in `backend/tests/`. All use `MockProvider(delay=0)`. Fixtures in `conftest.py`.
