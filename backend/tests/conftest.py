import pytest
from fastapi.testclient import TestClient

from core.db.database import Database
from core.llm.mock import MockProvider
from core.services.logger import SimulationLogger
from core.services.simulation import SimulationService


@pytest.fixture
def db(tmp_path):
    test_db = Database(str(tmp_path / "test.db"))
    test_db.init()
    yield test_db
    test_db.close()


@pytest.fixture
def mock_provider():
    return MockProvider(delay=0)


@pytest.fixture
def test_client(db):
    from backend.api.main import app
    import backend.api.dependencies
    import backend.api.routes.chat as chat_module
    import backend.api.routes.simulate as simulate_module

    original_deps_db = backend.api.dependencies.db
    original_chat_db = chat_module.db
    original_sim_db = simulate_module.db
    original_sim_service = simulate_module.simulation_service

    test_service = SimulationService(db, SimulationLogger())

    backend.api.dependencies.db = db
    chat_module.db = db
    simulate_module.db = db
    simulate_module.simulation_service = test_service

    with TestClient(app) as client:
        yield client

    backend.api.dependencies.db = original_deps_db
    chat_module.db = original_chat_db
    simulate_module.db = original_sim_db
    simulate_module.simulation_service = original_sim_service
