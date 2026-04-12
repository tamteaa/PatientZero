from __future__ import annotations

import json
from dataclasses import dataclass, field

from core.agents.base import AgentRuntime
from core.llm.base import LLMProvider
from core.llm.factory import parse_provider_model
from core.types import JudgeResult, Transcript

_BASE_TEMPLATE = """\
You are an evaluator assessing a multi-agent conversation.

## Rubric
{rubric}

## Instructions
{instructions}

## Response Format
Return valid JSON with this shape:
{{
  "scores": {{
{scores_schema}
  }},
  "justification": "<brief rationale or null>"
}}"""


def _normalize_rubric(rubric: list[str] | dict[str, str]) -> dict[str, str]:
    if isinstance(rubric, dict):
        if not rubric:
            raise ValueError("Judge rubric must be non-empty")
        return {str(k): str(v) for k, v in rubric.items()}
    if not rubric:
        raise ValueError("Judge rubric must be non-empty")
    return {str(name): f"Score the conversation on {name}." for name in rubric}


@dataclass
class Judge:
    rubric: list[str] | dict[str, str]
    instructions: str
    model: str | None = None
    _provider: LLMProvider | None = field(default=None, init=False, repr=False)
    _resolved_model: str | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.rubric = _normalize_rubric(self.rubric)

    @property
    def rubric_map(self) -> dict[str, str]:
        return dict(self.rubric)

    @property
    def system_prompt(self) -> str:
        rubric_block = "\n".join(
            f"- {name}: {description}" for name, description in self.rubric_map.items()
        )
        schema_lines = ",\n".join(
            f'    "{name}": <number or null>' for name in self.rubric_map
        )
        return _BASE_TEMPLATE.format(
            rubric=rubric_block,
            instructions=self.instructions,
            scores_schema=schema_lines,
        )

    def bind(self, provider: LLMProvider, model: str | None = None) -> "Judge":
        self._provider = provider
        self._resolved_model = model or self.model
        return self

    async def evaluate(self, transcript: Transcript) -> JudgeResult:
        provider = self._provider
        model = self._resolved_model or self.model
        if provider is None:
            if model is None:
                raise ValueError("Judge has no bound provider or model")
            provider, model = parse_provider_model(model)

        runtime = AgentRuntime(provider, model, self.system_prompt, name="judge")
        eval_message = f"## Transcript\n{json.dumps(transcript.to_dicts(), indent=2)}"
        trace = await runtime.respond([{"role": "user", "content": eval_message}])
        response = trace.output

        try:
            json_str = response
            if "```" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
            data = json.loads(json_str)
            result = JudgeResult.from_dict({"model": model, **data})
        except (json.JSONDecodeError, ValueError, TypeError):
            result = JudgeResult(
                model=model,
                scores={name: None for name in self.rubric_map},
                justification=f"Failed to parse evaluation response: {response}",
            )

        for name in self.rubric_map:
            result.scores.setdefault(name, None)
        return result


__all__ = ["Judge"]
