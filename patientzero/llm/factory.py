import os

from patientzero.llm.base import LLMProvider
from patientzero.llm.claude_cli_provider import ClaudeCLIProvider
from patientzero.llm.mock import MockProvider
from patientzero.llm.openai_provider import OpenAIProvider


_providers: dict[str, LLMProvider] = {}


def get_provider(provider_name: str) -> LLMProvider:
    if provider_name in _providers:
        return _providers[provider_name]

    match provider_name:
        case "mock":
            _providers[provider_name] = MockProvider()
        case "openai":
            _providers[provider_name] = OpenAIProvider(
                api_key=os.environ["OPENAI_API_KEY"],
            )
        case "kimi":
            _providers[provider_name] = OpenAIProvider(
                api_key=os.environ["KIMI_API_KEY"],
                base_url="https://api.kimi.com/coding/v1",
                default_headers={
                    "User-Agent": os.environ.get("KIMI_USER_AGENT", "claude-code/1.0"),
                    "X-Client-Name": os.environ.get("KIMI_CLIENT_NAME", "claude-code"),
                },
            )
        case "claude":
            _providers[provider_name] = ClaudeCLIProvider()
        case "local":
            _providers[provider_name] = OpenAIProvider(
                api_key="local",
                base_url=os.environ.get("LOCAL_LLM_URL", "http://localhost:11434") + "/v1",
            )
        case _:
            raise ValueError(f"Unknown LLM provider: {provider_name}")

    return _providers[provider_name]


def parse_provider_model(provider_model: str) -> tuple[LLMProvider, str]:
    """Parse 'provider:model' string and return (provider_instance, model_name)."""
    if ":" not in provider_model:
        return get_provider(provider_model), "default"
    provider_name, model_name = provider_model.split(":", 1)
    return get_provider(provider_name), model_name
