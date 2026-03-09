from pathlib import Path
from agents.base import Agent
from llm.base import LLMProvider

PROMPTS_DIR = Path(__file__).parent / "prompts"

PROMPT_FILES = {
    ("clinical", "static"): "explainer_clinical_static.txt",
    ("clinical", "dialog"): "explainer_clinical_dialog.txt",
    ("analogy", "static"): "explainer_analogy_static.txt",
    ("analogy", "dialog"): "explainer_analogy_dialog.txt",
}


class ExplainerAgent(Agent):
    def __init__(
        self,
        provider: LLMProvider,
        model: str,
        style: str,
        mode: str,
        scenario: dict,
    ):
        self.style = style
        self.mode = mode
        self.scenario = scenario
        system_prompt = self._build_system_prompt(style, mode, scenario)
        super().__init__(provider, model, system_prompt)

    @staticmethod
    def _build_system_prompt(style: str, mode: str, scenario: dict) -> str:
        key = (style, mode)
        if key not in PROMPT_FILES:
            raise ValueError(f"Invalid style/mode combination: {style}/{mode}")
        template_path = PROMPTS_DIR / PROMPT_FILES[key]
        template = template_path.read_text()
        return template.format(
            test_name=scenario.get("test_name", ""),
            results=scenario.get("results", ""),
            normal_range=scenario.get("normal_range", ""),
            significance=scenario.get("significance", ""),
        )
