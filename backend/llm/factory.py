import os

from llm.base import LLMProvider
from llm.mock import MockProvider
from llm.openai_provider import OpenAIProvider


_providers: dict[str, LLMProvider] = {}


def get_provider(provider_name: str) -> LLMProvider:
    if provider_name in _providers:
        return _providers[provider_name]

    match provider_name:
        case "mock":
            _providers[provider_name] = MockProvider()
        case "kimi":
            _providers[provider_name] = OpenAIProvider(
                api_key=os.environ["KIMI_API_KEY"],
                base_url="https://api.moonshot.cn/v1",
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
