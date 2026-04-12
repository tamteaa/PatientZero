import pytest

from core import Agent, Distribution, Experiment
from core.db.database import Database
from core.llm.mock import MockProvider
from core.repositories import RepoSet
from core.types import ExperimentConfig, JudgeConfig


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


@pytest.fixture
def db(tmp_path):
    test_db = Database(str(tmp_path / "test.db"))
    test_db.init()
    yield test_db
    test_db.close()


@pytest.fixture
def repos(db):
    return RepoSet.for_db(db)


@pytest.fixture
def experiment(repos):
    return Experiment(_test_config(), repos).record


@pytest.fixture
def mock_provider():
    return MockProvider(delay=0)
