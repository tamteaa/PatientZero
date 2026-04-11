import json
import uuid

from core.db.database import Database
from core.types import SimulationRecord, SimulationTurnRecord


def _sim(row) -> SimulationRecord | None:
    return SimulationRecord(**dict(row)) if row else None


def _turn(row) -> SimulationTurnRecord:
    return SimulationTurnRecord(**dict(row))


def create_simulation(
    db: Database,
    experiment_id: str,
    persona_name: str,
    scenario_name: str,
    model: str,
    config: dict,
    optimization_target_id: str | None = None,
) -> SimulationRecord:
    sim_id = str(uuid.uuid4())
    db.execute(
        """INSERT INTO simulations (
               id, experiment_id, persona_name, scenario_name, model, config_json, optimization_target_id
           ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            sim_id,
            experiment_id,
            persona_name,
            scenario_name,
            model,
            json.dumps(config),
            optimization_target_id,
        ),
    )
    return _sim(db.conn.execute("SELECT * FROM simulations WHERE id = ?", (sim_id,)).fetchone())


def complete_simulation(db: Database, sim_id: str, duration_ms: float) -> None:
    db.execute(
        """UPDATE simulations SET state = 'completed', duration_ms = ?, completed_at = datetime('now')
           WHERE id = ?""",
        (duration_ms, sim_id),
    )


def fail_simulation(db: Database, sim_id: str) -> None:
    db.execute(
        "UPDATE simulations SET state = 'error' WHERE id = ?",
        (sim_id,),
    )


def add_simulation_turn(
    db: Database,
    sim_id: str,
    turn_number: int,
    role: str,
    agent_type: str,
    content: str,
    duration_ms: float,
) -> None:
    db.execute(
        """INSERT INTO simulation_turns (simulation_id, turn_number, role, agent_type, content, duration_ms)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (sim_id, turn_number, role, agent_type, content, duration_ms),
    )


def get_simulation(db: Database, sim_id: str) -> SimulationRecord | None:
    return _sim(db.conn.execute("SELECT * FROM simulations WHERE id = ?", (sim_id,)).fetchone())


def list_simulations(db: Database) -> list[SimulationRecord]:
    rows = db.conn.execute("SELECT * FROM simulations ORDER BY created_at DESC, rowid DESC").fetchall()
    return [SimulationRecord(**dict(r)) for r in rows]


def get_simulation_turns(db: Database, sim_id: str) -> list[SimulationTurnRecord]:
    rows = db.conn.execute(
        "SELECT * FROM simulation_turns WHERE simulation_id = ? ORDER BY turn_number",
        (sim_id,),
    ).fetchall()
    return [_turn(r) for r in rows]


def delete_simulation(db: Database, sim_id: str) -> None:
    db.execute("DELETE FROM simulation_turns WHERE simulation_id = ?", (sim_id,))
    db.execute("DELETE FROM evaluations WHERE simulation_id = ?", (sim_id,))
    db.execute("DELETE FROM simulations WHERE id = ?", (sim_id,))
