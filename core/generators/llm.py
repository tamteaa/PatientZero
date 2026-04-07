import json

from core.generators.base import AsyncScenarioGenerator
from core.llm.base import LLMProvider
from core.types import Scenario

_SYSTEM_PROMPT = """\
You are a medical scenario generator. Generate realistic medical test result scenarios \
that a doctor would explain to a patient.

Each scenario should include:
- The medical test name
- Specific numeric results (some normal, some abnormal)
- The normal reference ranges
- Clinical significance of the findings

Generate diverse scenarios across different medical tests (blood work, metabolic panels, \
thyroid, liver, kidney, cardiac markers, urinalysis, etc.). Vary the severity and number \
of abnormal findings.

Respond with a JSON array of objects, each with "name" (short label) and "description" (full scenario text).
Example:
[
  {
    "name": "CBC - Elevated WBC",
    "description": "Medical Test: Complete Blood Count\\nResults: WBC: 14.2 (H), RBC: 4.5, ...\\nNormal Range: ...\\nClinical Significance: ..."
  }
]

Return ONLY valid JSON. No markdown, no code fences, no explanation."""


class LLMScenarioGenerator(AsyncScenarioGenerator):
    """Generates scenarios by prompting an LLM."""

    def __init__(self, provider: LLMProvider, model: str):
        self.provider = provider
        self.model = model

    async def generate(self, n: int = 1) -> list[Scenario]:
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"Generate {n} medical test result scenario(s)."},
        ]

        chunks: list[str] = []
        async for token in self.provider.stream(messages, self.model):
            chunks.append(token)

        raw = "".join(chunks).strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            if raw.endswith("```"):
                raw = raw[:-3]

        data = json.loads(raw)
        if isinstance(data, dict):
            data = [data]

        return [Scenario(name=item["name"], description=item["description"]) for item in data]
