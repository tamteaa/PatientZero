from core.llm import dspy_adapter


def test_dspy_package_available():
    assert dspy_adapter.dspy_available()
    assert dspy_adapter.get_dspy() is not None
