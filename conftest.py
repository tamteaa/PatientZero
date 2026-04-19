import pytest_asyncio

from patientzero import Agent, Distribution, Experiment
from patientzero.db.database import Database
from patientzero.llm.mock import MockProvider
from patientzero.repositories import RepoSet
from patientzero.types import ExperimentConfig, JudgeConfig


def _test_config() -> ExperimentConfig:
    return ExperimentConfig(
        name="test-exp",
        agents=(
            Agent(
                "doctor",
                "Doctor {empathy}",
                Distribution(empathy={"low": 0.5, "high": 0.5}),
            ),
            Agent(
                "patient",
                "Patient {literacy}",
                Distribution(literacy={"low": 0.5, "high": 0.5}),
            ),
        ),
        judge=JudgeConfig(
            rubric={"score": "Overall."},
            instructions="Evaluate the transcript.",
            model=None,
        ),
        model="mock:default",
    )


@pytest_asyncio.fixture
async def db(tmp_path):
    test_db = Database(str(tmp_path / "test.db"))
    await test_db.init()
    yield test_db
    await test_db.close()


@pytest_asyncio.fixture
async def repos(db):
    return RepoSet.for_db(db)


@pytest_asyncio.fixture
async def experiment(db):
    exp = await Experiment.create(_test_config(), db)
    return exp.record


@pytest_asyncio.fixture
async def mock_provider():
    return MockProvider(delay=0)
