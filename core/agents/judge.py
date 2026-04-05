import json
from core.agents.base import Agent
from core.agents.prompts import JUDGE_BASE
from core.llm.base import LLMProvider
from core.types import Transcript


class JudgeAgent(Agent):
    def __init__(self, provider: LLMProvider, model: str):
        super().__init__(provider, model, JUDGE_BASE)

    async def evaluate(self, transcript: Transcript) -> dict:
        eval_message = (
            f"## Transcript\n{json.dumps(transcript.to_dicts(), indent=2)}"
        )
        messages = [{"role": "user", "content": eval_message}]
        trace = await self.respond(messages)
        response = trace.output

        try:
            json_str = response
            if "```" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            return {
                "comprehension_score": None,
                "factual_recall": None,
                "applied_reasoning": None,
                "explanation_quality": None,
                "interaction_quality": None,
                "confidence_comprehension_gap": None,
                "justification": f"Failed to parse evaluation response: {response}",
            }
