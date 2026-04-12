"""
Feedback — pure prompt-optimization step.

Takes the current optimization target (the prompts in use) and a list of
completed simulation traces (profiles + transcript + judge scores +
justification). Calls an LLM once; returns the proposed new prompts and a
short rationale. No DB, no persistence — the service layer writes the row.
"""

from __future__ import annotations

import json

from core.agents.base import AgentRuntime
from core.llm.factory import parse_provider_model
from core.types import FeedbackTrace, OptimizationTarget


_SYSTEM_PROMPT = """\
You are a prompt optimizer. You are given:

  1. The current system prompts for a set of agents that converse in a
     multi-turn simulation.
  2. A collection of recent completed simulations, each with the sampled
     agent profiles, the full transcript, the judge's per-dimension
     scores, and the judge's written justification.

Propose a rewrite of every prompt that should improve the judge's scores
across future simulations. Hard constraints:

  - The new prompts MUST preserve every {field} placeholder that appears
    in the originals. Do not add new placeholders.
  - Every agent listed in the current prompts must appear in your output.
  - Return ONLY valid JSON with exactly this shape and no extra keys:

      {
        "prompts": {
          "<agent_name>": "<new prompt text>",
          ...
        },
        "rationale": "<one paragraph explaining the edit>"
      }

  - No markdown, no code fences, no commentary outside the JSON.
"""


class Feedback:
    async def run(
        self,
        current_target: OptimizationTarget,
        traces: list[FeedbackTrace],
        model: str,
    ) -> tuple[dict[str, str], str]:
        user_message = self._build_user_message(current_target, traces)
        provider, model_name = parse_provider_model(model)
        runtime = AgentRuntime(provider, model_name, _SYSTEM_PROMPT, name="feedback")
        step = await runtime.respond([{"role": "user", "content": user_message}])

        data = self._parse(step.output)

        prompts = data.get("prompts")
        if not isinstance(prompts, dict):
            raise ValueError(f"Feedback LLM returned no 'prompts' object: {step.output[:500]}")
        missing = set(current_target.prompts) - set(prompts)
        if missing:
            raise ValueError(
                f"Feedback LLM dropped agents {sorted(missing)} from its rewrite"
            )
        for name, text in prompts.items():
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f"Feedback LLM returned empty prompt for agent {name!r}")
            self._check_placeholders(name, current_target.prompts[name], text)

        rationale = str(data.get("rationale") or "")
        return {k: prompts[k] for k in current_target.prompts}, rationale

    # ── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _parse(raw: str) -> dict:
        text = raw.strip()
        if text.startswith("```"):
            first = text.find("{")
            last = text.rfind("}")
            if first != -1 and last != -1:
                text = text[first:last + 1]
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Feedback LLM returned invalid JSON: {exc}\n{raw[:500]}") from exc

    @staticmethod
    def _check_placeholders(name: str, original: str, rewrite: str) -> None:
        import string
        def fields(s: str) -> set[str]:
            out: set[str] = set()
            for _, field_name, _, _ in string.Formatter().parse(s):
                if field_name:
                    out.add(field_name.split(".", 1)[0].split("[", 1)[0])
            return out
        original_fields = fields(original)
        rewrite_fields = fields(rewrite)
        dropped = original_fields - rewrite_fields
        if dropped:
            raise ValueError(
                f"Feedback rewrite for agent {name!r} dropped required fields: {sorted(dropped)}"
            )

    @staticmethod
    def _build_user_message(
        current_target: OptimizationTarget,
        traces: list[FeedbackTrace],
    ) -> str:
        parts: list[str] = ["## Current prompts\n"]
        for agent_name, prompt in current_target.prompts.items():
            parts.append(f"### {agent_name}\n{prompt}\n")

        parts.append(f"\n## Traces ({len(traces)})\n")
        if not traces:
            parts.append("(no completed simulations yet — propose a modest edit based on the current prompts alone)\n")
        for i, trace in enumerate(traces, start=1):
            parts.append(f"\n### Trace {i} — simulation {trace.simulation_id}\n")
            parts.append("Profiles:\n")
            for agent_name, traits in trace.profiles.items():
                parts.append(f"  {agent_name}:\n")
                for trait, value in traits.items():
                    if "\n" in str(value):
                        indented = "\n".join("      " + line for line in str(value).splitlines())
                        parts.append(f"    {trait}: |\n{indented}\n")
                    else:
                        parts.append(f"    {trait}: {value}\n")
            parts.append("Transcript:\n")
            for msg in trace.transcript:
                parts.append(f"  [{msg.role}] {msg.content}\n")
            parts.append(f"Scores: {json.dumps(trace.scores)}\n")
            if trace.justification:
                parts.append(f"Judge: {trace.justification}\n")

        parts.append("\n## Your task\nReturn the JSON described in the system prompt now.\n")
        return "".join(parts)
