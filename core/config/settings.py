import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")
DB_PATH = os.getenv("DB_PATH", "patientzero.db")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

AVAILABLE_MODELS = [
    "mock:default",
    "kimi:kimi-k2.5",
    "openai:gpt-4o",
    "claude:claude-sonnet-4-20250514",
    "claude:claude-opus-4-20250514",
    "claude:claude-haiku-4-5-20251001",
    "local:default",
]

EXPLANATION_STYLES = [
    "clinical",
    "empathetic",
    "analogy",
    "simplified",
]
