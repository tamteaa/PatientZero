import pytest
from fastapi.testclient import TestClient

from db.database import Database
from llm.mock import MockProvider


@pytest.fixture
def db(tmp_path):
    test_db = Database(str(tmp_path / "test.db"))
    test_db.init()
    yield test_db
    test_db.close()


@pytest.fixture
def mock_provider():
    return MockProvider()


@pytest.fixture
def test_client(db):
    from api.main import app
    import api.dependencies
    import api.routes.chat as chat_module

    # Swap the DB in both the dependencies module and the routes module
    # (routes import db at module level, so we must patch both references)
    original_deps_db = api.dependencies.db
    original_chat_db = chat_module.db
    api.dependencies.db = db
    chat_module.db = db

    with TestClient(app) as client:
        yield client

    api.dependencies.db = original_deps_db
    chat_module.db = original_chat_db
