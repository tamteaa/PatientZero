# Implementation Overview

## Stack
- **Frontend**: React + Vite + TypeScript
- **Backend**: FastAPI
- **LLM**: TBD
- **Repo**: Monorepo

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                    React Frontend                     │
│  - Chat interface (validation study + demo)           │
│  - Simulation dashboard (run/monitor sessions)        │
│  - Results viewer (scores, transcripts, comparisons)  │
└────────────────────────┬─────────────────────────────┘
                         │ REST / SSE
┌────────────────────────┴─────────────────────────────┐
│                    Backend API                        │
│  - Session management                                 │
│  - Agent orchestration                                │
│  - Data storage                                       │
├──────────────┬──────────────┬───────────────┤
│  Explainer   │   Patient    │    Judge       │
│  Agent       │   Agent      │    Agent       │
│  (4 modes)   │ (12 personas)│  (evaluator)   │
└──────────────┴──────────────┴───────────────┘
```

## Monorepo Structure

```
PatientZero/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat/            # Chat bubbles, input, typing indicator
│   │   │   ├── dashboard/       # Session cards, progress bars, filters
│   │   │   ├── results/         # Score tables, transcript viewer
│   │   │   ├── personas/        # Persona cards, trait badges
│   │   │   ├── scenarios/       # Scenario selector, detail view
│   │   │   └── common/          # Layout, nav, buttons, modals
│   │   ├── pages/
│   │   │   ├── Home.tsx
│   │   │   ├── Simulation.tsx   # Run & monitor simulation sessions
│   │   │   ├── Chat.tsx         # Live chat for validation study
│   │   │   ├── Results.tsx      # View scores, transcripts, comparisons
│   │   │   ├── Personas.tsx     # Browse & inspect personas
│   │   │   └── Validation.tsx   # NVS test + participant flow
│   │   ├── hooks/
│   │   │   ├── useSession.ts
│   │   │   ├── useChat.ts
│   │   │   └── useResults.ts
│   │   ├── api/
│   │   │   ├── client.ts        # Axios/fetch wrapper
│   │   │   ├── sessions.ts      # Session endpoints
│   │   │   ├── personas.ts      # Persona endpoints
│   │   │   └── results.ts       # Results endpoints
│   │   ├── types/
│   │   │   ├── session.ts
│   │   │   ├── persona.ts
│   │   │   ├── scenario.ts
│   │   │   └── score.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── backend/
│   ├── types/
│   │   ├── session.py           # Session, Turn, Transcript models
│   │   ├── persona.py           # Persona, Demographics models
│   │   ├── scenario.py          # Scenario, LabData models
│   │   ├── score.py             # ComprehensionScore, QualityScore models
│   │   └── condition.py         # ExplanationStyle, InteractionMode enums
│   ├── config/
│   │   └── settings.py          # Env vars, model params, constants
│   ├── agents/
│   │   ├── explainer.py         # Explainer Agent
│   │   ├── patient.py           # Patient Agent
│   │   └── judge.py             # Judge Agent
│   ├── engine/
│   │   ├── interaction.py       # Orchestrator (static + dialog flows)
│   │   ├── session.py           # Session lifecycle management
│   │   └── logger.py            # Transcript & metric logging
│   ├── scenarios/
│   │   ├── cbc_blood_test.json
│   │   ├── pre_diabetes.json
│   │   └── medication.json
│   ├── personas/
│   │   ├── definitions.json     # All 12 persona specs
│   │   └── templates.py         # System prompt builders
│   ├── evaluation/
│   │   ├── answer_keys.json
│   │   ├── scoring.py           # Score computation
│   │   ├── calibration.py       # Adversarial judge tests
│   │   └── consistency.py       # Judge re-run consistency
│   ├── analysis/
│   │   ├── stats.py             # ANOVA, bootstrap CIs, effect sizes
│   │   ├── plots.py             # Visualization
│   │   └── report.py            # Results summary generation
│   ├── validation/
│   │   ├── nvs_test.py          # NVS literacy assessment
│   │   └── comparison.py        # Sim vs real (ICC, Kendall's τ)
│   ├── api/
│   │   ├── routes/
│   │   │   ├── sessions.py      # /sessions CRUD + run
│   │   │   ├── personas.py      # /personas list + detail
│   │   │   ├── scenarios.py     # /scenarios list + detail
│   │   │   ├── results.py       # /results scores + transcripts
│   │   │   └── validation.py    # /validation participant flow
│   │   └── main.py              # FastAPI app entry
│   ├── db/
│   │   ├── database.py          # Database class (connection, init, migrations)
│   │   ├── schema.sql           # Table definitions
│   │   └── queries/
│   │       ├── sessions.py      # Session CRUD queries
│   │       ├── personas.py      # Persona queries
│   │       ├── scenarios.py     # Scenario queries
│   │       ├── scores.py        # Score queries
│   │       └── participants.py  # Validation participant queries
│   └── pyproject.toml
│
├── plan/
├── report.txt
├── README.md
└── .gitignore
```

## Frontend Packages

| Package | Purpose |
|---------|---------|
| `react-router-dom` | Page routing |
| `axios` | HTTP client |
| `@tanstack/react-query` | Server state, caching, refetching |
| `tailwindcss` | Styling |
| `shadcn/ui` | Component library (built on Radix + Tailwind) |
| `recharts` | Charts for results/analysis |
| `eventsource-parser` | SSE parsing for streaming responses |
| `lucide-react` | Icons |
| `clsx` / `tailwind-merge` | Conditional class names |

## Backend Packages

| Package | Purpose |
|---------|---------|
| `fastapi` | API framework |
| `uvicorn` | ASGI server |
| `pydantic` | Data validation & serialization |
| `sse-starlette` | Server-Sent Events for streaming |
| `anthropic` | Claude API (or `openai` — TBD) |
| `scipy` | Statistical tests (ANOVA, Kruskal-Wallis) |
| `numpy` | Numerical computation |
| `pandas` | Data manipulation |
| `pingouin` | ANOVA, effect sizes, ICC |
| `matplotlib` | Plotting |
| `seaborn` | Statistical visualization |
| `python-dotenv` | Env file loading |

## Build Order

| Phase | What | Description |
|-------|------|-------------|
| 1 | Project scaffolding | Monorepo setup, frontend + backend boilerplate |
| 2 | Core agents | Explainer, Patient, Judge agents with prompt engineering |
| 3 | Scenarios & personas | Medical content, answer keys, 12 persona definitions |
| 4 | Interaction engine | Orchestrator for static & dialog sessions |
| 5 | Backend API | Endpoints for running sessions, fetching results |
| 6 | Frontend — Chat UI | Chat interface for validation study + live demo |
| 7 | Frontend — Dashboard | Run simulations, monitor progress, view transcripts |
| 8 | Judge & evaluation | Scoring pipeline, calibration, consistency checks |
| 9 | Analysis | Statistical tests, plots, result generation |
| 10 | Validation | NVS test interface, real participant flow, comparison |

## Open Questions
- [x] Backend framework: FastAPI
- [ ] LLM provider: Claude (Anthropic) / OpenAI / configurable?
- [x] Database: SQLite, raw queries, `db/` directory with Database class
- [x] Real-time streaming: SSE
- [x] Auth: None for now
