# CLAUDE.md

## Project: PatientZero

Research simulation system studying how AI explanation styles (clinical vs analogy) and interaction modes (static vs dialog) affect patient comprehension of medical information.

## Repo Layout

This is a git submodule inside the parent `AI_Capstone` repo.

```
project/
├── backend/       # Python FastAPI server (run from here)
├── frontend/      # React + Vite + TypeScript app
├── plan/          # Implementation plans
└── report.txt     # Research report
```

## Backend

- **Language**: Python 3.12+, managed with `uv`
- **Framework**: FastAPI with SSE streaming responses
- **Database**: SQLite (WAL mode), raw SQL queries (no ORM)
- **Working directory**: Always `cd backend/` before running commands
- **Run server**: `uv run uvicorn api.main:app --reload`
- **Run tests**: `uv run python -m pytest tests/ -v`
- **Install deps**: `uv sync`

### LLM Provider Architecture

Factory pattern with abstract base class:

- `llm/base.py` — `LLMProvider` ABC with `async stream()` method
- `llm/factory.py` — `get_provider()` singleton factory + `parse_provider_model()` parser
- `llm/mock.py` — `MockProvider` for testing (hardcoded responses)
- `llm/openai_provider.py` — `OpenAIProvider` wrapping `AsyncOpenAI`, used for any OpenAI-compatible API

**Models use `"provider:model"` string format** (e.g., `"kimi:kimi-2.5"`). Parsed by `parse_provider_model()`.

**Current providers**: `mock`, `kimi` (Moonshot API via OpenAI-compatible client). `claude` and `local` are listed in AVAILABLE_MODELS but not yet implemented.

### Adding a new LLM provider

1. Create `llm/<name>.py` implementing `LLMProvider.stream()`
2. Add a `case` in `llm/factory.py:get_provider()`
3. Add model strings to `config/settings.py:AVAILABLE_MODELS`
4. Add env vars to `.env.example`

### Agents

Three agent types built on `agents/base.py`:
- **PatientAgent** — simulates patients with dynamic personas
- **ExplainerAgent** — explains medical test results (4 prompt variants)
- **JudgeAgent** — evaluates patient comprehension, returns JSON

### API

All endpoints prefixed with `/api`. Chat uses SSE streaming. Sessions store model selection.

## Frontend

- React + Vite + TypeScript
- Tailwind CSS + shadcn/ui components
- `npm install && npm run dev` to run (port 5173)

## Environment

Config via `.env` file at project root (see `.env.example`). Key vars:
- `KIMI_API_KEY` — for Moonshot/Kimi provider
- `ANTHROPIC_API_KEY` — for Claude provider (not yet implemented)
- `LLM_PROVIDER` — active default provider (`mock` by default)

## Testing

53 tests covering agents, API routes, DB queries, and LLM factory. All use mock provider. Test fixtures in `backend/tests/conftest.py` handle temp DB and mock provider injection.
