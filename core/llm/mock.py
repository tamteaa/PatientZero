import asyncio
import json
import random
import re
from collections.abc import AsyncGenerator

from core.llm.base import LLMProvider

# Detect judge system prompts by the fixed schema skeleton emitted by
# ``core.judge.Judge.system_prompt``. Each rubric dimension line has the
# literal form ``"<name>": <number or null>`` — capture them.
_JUDGE_SCORE_LINE = re.compile(r'"([A-Za-z_][A-Za-z0-9_]*)":\s*<number or null>')


class MockProvider(LLMProvider):
    def __init__(self, delay: float = 0.03, seed: int | None = None):
        self.delay = delay
        self._rng = random.Random(seed)

    async def stream(self, messages: list[dict], model: str) -> AsyncGenerator[str, None]:
        response = self._make_response(messages, model)
        for word in response.split():
            yield word + " "
            if self.delay:
                await asyncio.sleep(self.delay)

    # ── Response shaping ────────────────────────────────────────────────────

    def _make_response(self, messages: list[dict], model: str) -> str:
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        rubric_keys = _JUDGE_SCORE_LINE.findall(system)
        if rubric_keys:
            return self._judge_json(rubric_keys)
        last_user = next(
            (m["content"] for m in reversed(messages) if m["role"] != "system"),
            "",
        )
        return (
            f"[mock:{model}] This is a mock response to: \"{last_user[:80]}\". "
            "Simulated output for testing."
        )

    def _judge_json(self, dims: list[str]) -> str:
        scores = {dim: self._rng.randint(55, 95) for dim in dims}
        payload = {
            "scores": scores,
            "justification": "Mock evaluation: scores drawn uniformly from [55, 95].",
        }
        return json.dumps(payload)
