import pytest
from core.generators.static import StaticScenarioGenerator
from core.types import Scenario


@pytest.mark.asyncio
async def test_generates_one():
    gen = StaticScenarioGenerator()
    scenarios = await gen.generate(1)
    assert len(scenarios) == 1
    assert isinstance(scenarios[0], Scenario)


@pytest.mark.asyncio
async def test_generates_multiple():
    gen = StaticScenarioGenerator()
    scenarios = await gen.generate(5)
    assert len(scenarios) == 5


@pytest.mark.asyncio
async def test_scenario_has_content():
    gen = StaticScenarioGenerator()
    scenarios = await gen.generate(1)
    s = scenarios[0]
    assert len(s.name) > 0
    assert len(s.description) > 0
    assert "Medical Test:" in s.description
    assert "Results:" in s.description


@pytest.mark.asyncio
async def test_high_abnormal_ratio():
    gen = StaticScenarioGenerator(abnormal_ratio=1.0)
    scenarios = await gen.generate(3)
    for s in scenarios:
        assert "(H)" in s.description or "(L)" in s.description


@pytest.mark.asyncio
async def test_zero_abnormal_ratio():
    gen = StaticScenarioGenerator(abnormal_ratio=0.0)
    scenarios = await gen.generate(3)
    for s in scenarios:
        assert "(H)" not in s.description
        assert "(L)" not in s.description
