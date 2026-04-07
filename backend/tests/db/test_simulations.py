from core.db.queries.simulations import (
    add_simulation_turn,
    complete_simulation,
    create_simulation,
    delete_simulation,
    fail_simulation,
    get_simulation,
    get_simulation_turns,
    list_simulations,
)
from core.types import SimulationRecord, SimulationTurnRecord


def test_create_simulation(db):
    sim = create_simulation(
        db,
        persona_name="Maria Santos",
        scenario_name="CBC",
        model="mock:default",
        config={"persona": {}, "scenario": {}},
    )
    assert isinstance(sim, SimulationRecord)
    assert sim.id is not None
    assert sim.persona_name == "Maria Santos"
    assert sim.state == "running"


def test_complete_simulation(db):
    sim = create_simulation(db, "Maria", "CBC", "mock:default", {})
    complete_simulation(db, sim.id, 1234.5)
    updated = get_simulation(db, sim.id)
    assert updated.state == "completed"
    assert updated.duration_ms == 1234.5
    assert updated.completed_at is not None


def test_fail_simulation(db):
    sim = create_simulation(db, "Maria", "CBC", "mock:default", {})
    fail_simulation(db, sim.id)
    updated = get_simulation(db, sim.id)
    assert updated.state == "error"


def test_add_and_get_turns(db):
    sim = create_simulation(db, "Maria", "CBC", "mock:default", {})
    add_simulation_turn(db, sim.id, 0, "doctor", "DoctorAgent", "Hello", 100.0)
    add_simulation_turn(db, sim.id, 1, "patient", "PatientAgent", "Hi", 200.0)

    turns = get_simulation_turns(db, sim.id)
    assert len(turns) == 2
    assert isinstance(turns[0], SimulationTurnRecord)
    assert turns[0].role == "doctor"
    assert turns[0].agent_type == "DoctorAgent"
    assert turns[0].content == "Hello"
    assert turns[0].duration_ms == 100.0
    assert turns[1].role == "patient"
    assert turns[1].turn_number == 1


def test_list_simulations(db):
    create_simulation(db, "Maria", "CBC", "mock:default", {})
    create_simulation(db, "James", "HbA1c", "mock:default", {})
    sims = list_simulations(db)
    assert len(sims) == 2
    assert sims[0].persona_name == "James"


def test_get_simulation_not_found(db):
    assert get_simulation(db, "nonexistent") is None


def test_delete_simulation(db):
    sim = create_simulation(db, "Maria", "CBC", "mock:default", {})
    add_simulation_turn(db, sim.id, 0, "doctor", "DoctorAgent", "Hello", 100.0)
    delete_simulation(db, sim.id)
    assert get_simulation(db, sim.id) is None
    assert get_simulation_turns(db, sim.id) == []
