import json
from pathlib import Path
from agents.base import Agent
from llm.base import LLMProvider

PROMPTS_DIR = Path(__file__).parent / "prompts"


class JudgeAgent(Agent):
    def __init__(self, provider: LLMProvider, model: str):
        template_path = PROMPTS_DIR / "judge_base.txt"
        system_prompt = template_path.read_text()
        super().__init__(provider, model, system_prompt)

    async def evaluate(
        self,
        transcript: list[dict],
        quiz_responses: list[dict],
        answer_key: list[dict],
        mode: str,
    ) -> dict:
        eval_message = (
            f"## Mode\n{mode}\n\n"
            f"## Transcript\n{json.dumps(transcript, indent=2)}\n\n"
            f"## Quiz Responses\n{json.dumps(quiz_responses, indent=2)}\n\n"
            f"## Answer Key\n{json.dumps(answer_key, indent=2)}"
        )
        messages = [{"role": "user", "content": eval_message}]
        response = await self.respond(messages)

        # Extract JSON from the response
        try:
            # Try to find JSON in the response (may be wrapped in markdown code block)
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
