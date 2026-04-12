import pytest
from patientzero.llm.factory import get_provider, parse_provider_model, _providers
from patientzero.llm.mock import MockProvider


@pytest.fixture(autouse=True)
def clear_provider_cache():
    _providers.clear()
    yield
    _providers.clear()


def test_get_provider_mock():
    provider = get_provider("mock")
    assert isinstance(provider, MockProvider)


def test_get_provider_unknown_raises():
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        get_provider("nonexistent")


def test_provider_caching():
    p1 = get_provider("mock")
    p2 = get_provider("mock")
    assert p1 is p2


def test_parse_provider_model_with_colon():
    provider, model = parse_provider_model("mock:default")
    assert isinstance(provider, MockProvider)
    assert model == "default"


def test_parse_provider_model_without_colon():
    provider, model = parse_provider_model("mock")
    assert isinstance(provider, MockProvider)
    assert model == "default"


def test_parse_provider_model_with_complex_model():
    provider, model = parse_provider_model("mock:some-model-v2")
    assert isinstance(provider, MockProvider)
    assert model == "some-model-v2"
