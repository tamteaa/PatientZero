# PatientZero

Explaining Health: How AI Explanation Styles and Interaction Modalities Affect User Comprehension of Medical Information

## Overview

A simulation system that tests how different AI explanation styles (clinical vs. analogy-based) and interaction modes (static reading vs. interactive dialog) affect patient comprehension of medical information. Uses LLM-powered agents to simulate patient-doctor explanation scenarios.

## Tech Stack

- **Frontend**: React + Vite + TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: Python, FastAPI, SQLite
- **LLM**: Abstracted provider layer (Mock, OpenAI, Claude, Local)

## Project Structure

```
PatientZero/
├── core/              # Domain logic (imported by the backend)
├── frontend/          # React app
├── backend/           # FastAPI HTTP layer
├── plan/              # Implementation plans
└── report.txt         # Research report
```

## Prerequisites

- Python 3.12+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/) (Python package manager)

## Quick Start

1. Clone the repo:
```bash
git clone https://github.com/tamteaa/PatientZero.git
cd PatientZero
```

2. Set up environment:
```bash
cp .env.example .env
```

3. Install Python deps and start the backend (from the repo root so `core` imports resolve):
```bash
uv sync
uv run uvicorn backend.api.main:app --reload
```

4. Start the frontend:
```bash
cd frontend
npm install
npm run dev
```

5. Open http://localhost:5173

## License

MIT
