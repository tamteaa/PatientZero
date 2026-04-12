import pytest
from fastapi.testclient import TestClient

from patientzero.llm import factory as llm_factory
from patientzero.llm.mock import MockProvider
from patientzero.repositories import RepoSet
from patientzero.logger import SimulationLogger


@pytest.fixture
def test_client(db):
    import backend.api.main as main_module
    from backend.api.main import app
    import backend.api.dependencies
    import backend.api.routes.chat as chat_module
    import backend.api.routes.simulate as simulate_module
    import backend.api.routes.experiments as experiments_module
    import backend.api.routes.analysis as analysis_module

    original = {
        "deps_db": backend.api.dependencies.db,
        "deps_repos": backend.api.dependencies.repos,
        "deps_logger": backend.api.dependencies.logger,
        "main_db": main_module.db,
        "main_repos": main_module.repos,
        "chat_db": chat_module.db,
        "simulate_repos": simulate_module.repos,
        "simulate_logger": simulate_module.logger,
        "experiments_repos": experiments_module.repos,
        "analysis_repos": analysis_module.repos,
    }

    test_repos = RepoSet.for_db(db)
    test_logger = SimulationLogger()

    backend.api.dependencies.db = db
    backend.api.dependencies.repos = test_repos
    backend.api.dependencies.logger = test_logger
    main_module.db = db
    main_module.repos = test_repos
    chat_module.db = db
    simulate_module.repos = test_repos
    simulate_module.logger = test_logger
    experiments_module.repos = test_repos
    analysis_module.repos = test_repos

    # Seed the factory cache with a zero-delay mock so simulations
    # complete fast enough for synchronous test polling.
    llm_factory._providers["mock"] = MockProvider(delay=0)

    with TestClient(app) as client:
        yield client

    llm_factory._providers.pop("mock", None)

    backend.api.dependencies.db = original["deps_db"]
    backend.api.dependencies.repos = original["deps_repos"]
    backend.api.dependencies.logger = original["deps_logger"]
    main_module.db = original["main_db"]
    main_module.repos = original["main_repos"]
    chat_module.db = original["chat_db"]
    simulate_module.repos = original["simulate_repos"]
    simulate_module.logger = original["simulate_logger"]
    experiments_module.repos = original["experiments_repos"]
    analysis_module.repos = original["analysis_repos"]
