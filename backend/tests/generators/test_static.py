import pytest
from core.generators.static import StaticScenarioGenerator
from core.types import Scenario


def test_generates_one():
    gen = StaticScenarioGenerator()
    scenarios = gen.generate(1)
    assert len(scenarios) == 1
    assert isinstance(scenarios[0], Scenario)


def test_generates_multiple():
    gen = StaticScenarioGenerator()
    scenarios = gen.generate(5)
    assert len(scenarios) == 5


def test_scenario_has_content():
    gen = StaticScenarioGenerator()
    scenarios = gen.generate(1)
    s = scenarios[0]
    assert len(s.name) > 0
    assert len(s.description) > 0
    assert "Medical Test:" in s.description
    assert "Results:" in s.description


def test_high_abnormal_ratio():
    gen = StaticScenarioGenerator(abnormal_ratio=1.0)
    scenarios = gen.generate(3)
    for s in scenarios:
        assert "(H)" in s.description or "(L)" in s.description


def test_zero_abnormal_ratio():
    gen = StaticScenarioGenerator(abnormal_ratio=0.0)
    scenarios = gen.generate(3)
    for s in scenarios:
        assert "(H)" not in s.description
        assert "(L)" not in s.description
