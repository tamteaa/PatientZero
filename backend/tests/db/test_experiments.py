from core.db.queries.experiments import (
    create_experiment,
    delete_experiment,
    get_experiment,
    list_experiments,
)
from core.db.queries.simulations import (
    add_simulation_turn,
    create_simulation,
    get_simulation,
    get_simulation_turns,
)
from core.types import ExperimentRecord


def test_create_experiment(db):
    exp = create_experiment(db, name="baseline")
    assert isinstance(exp, ExperimentRecord)
    assert exp.id is not None
    assert exp.name == "baseline"
    assert exp.created_at is not None


def test_get_experiment(db):
    exp = create_experiment(db, name="baseline")
    fetched = get_experiment(db, exp.id)
    assert fetched is not None
    assert fetched.id == exp.id
    assert fetched.name == "baseline"


def test_get_experiment_not_found(db):
    assert get_experiment(db, "nonexistent") is None


def test_list_experiments(db):
    create_experiment(db, "a")
    create_experiment(db, "b")
    exps = list_experiments(db)
    assert len(exps) == 2
    # Newest first
    assert exps[0].name == "b"


def test_delete_experiment_cascades(db):
    exp = create_experiment(db, "baseline")
    sim = create_simulation(db, exp.id, "Maria", "CBC", "mock:default", {})
    add_simulation_turn(db, sim.id, 0, "doctor", "DoctorAgent", "Hello", 100.0)

    delete_experiment(db, exp.id)

    assert get_experiment(db, exp.id) is None
    assert get_simulation(db, sim.id) is None
    assert get_simulation_turns(db, sim.id) == []
