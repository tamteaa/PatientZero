from pathlib import Path
from agents.base import Agent
from llm.base import LLMProvider

PROMPTS_DIR = Path(__file__).parent / "prompts"


class PatientAgent(Agent):
    def __init__(self, provider: LLMProvider, model: str, persona: dict):
        self.persona = persona
        system_prompt = self._build_system_prompt(persona)
        super().__init__(provider, model, system_prompt)

    @staticmethod
    def _build_system_prompt(persona: dict) -> str:
        template_path = PROMPTS_DIR / "patient_base.txt"
        template = template_path.read_text()
        return template.format(
            name=persona.get("name", "Patient"),
            age=persona.get("age", "Unknown"),
            education=persona.get("education", "Unknown"),
            literacy_level=persona.get("literacy_level", "moderate"),
            anxiety=persona.get("anxiety", "moderate"),
            prior_knowledge=persona.get("prior_knowledge", "none"),
            communication_style=persona.get("communication_style", "neutral"),
            backstory=persona.get("backstory", "No additional background."),
        )
