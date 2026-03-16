# PatientZero Backend

FastAPI server with SQLite database and abstracted LLM provider layer.

## Setup

```bash
uv sync
cp ../.env.example ../.env  # if not done already
```

## Running

```bash
uv run uvicorn api.main:app --reload

```

Server runs at http://localhost:8000

## Project Structure

```
backend/
├── api/
│   ├── main.py              # FastAPI app, CORS, lifespan
│   ├── dependencies.py      # Shared db + provider instances
│   └── routes/
│       └── chat.py          # Chat + session endpoints
├── config/
│   └── settings.py          # Environment config
├── db/
│   ├── database.py          # Database class (SQLite, raw queries)
│   ├── schema.sql           # Table definitions
│   └── queries/
│       └── sessions.py      # Session + turn CRUD
├── llm/
│   ├── base.py              # Abstract LLMProvider
│   ├── mock.py              # Mock provider (testing)
│   └── factory.py           # Provider factory
└── pyproject.toml
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/sessions` | Create a new chat session |
| `GET` | `/api/sessions` | List all sessions |
| `GET` | `/api/sessions/{id}` | Get session with turns |
| `POST` | `/api/chat` | Send message, receive SSE stream |

## LLM Providers

Set `LLM_PROVIDER` in `.env`:

| Provider | Value | Status |
|----------|-------|--------|
| Mock | `mock` | Available |
| OpenAI | `openai` | Planned |
| Claude | `claude` | Planned |
| Local | `local` | Planned |

## Database

SQLite with WAL mode. Tables:

- `sessions` — chat sessions (id, title, created_at)
- `turns` — individual messages (session_id, role, content, turn_number)

Database file is created automatically on first run.
