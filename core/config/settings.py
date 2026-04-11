import os
from dotenv import load_dotenv

from core.types.settings import AppSettings

load_dotenv()


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or str(raw).strip() == "":
        return default
    return int(raw)


APP_SETTINGS = AppSettings(
    max_concurrent_simulations=_int_env("MAX_CONCURRENT_SIMULATIONS", 5),
    max_concurrent_optimizations=_int_env("MAX_CONCURRENT_OPTIMIZATIONS", 1),
)

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
