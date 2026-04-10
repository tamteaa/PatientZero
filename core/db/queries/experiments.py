import json
import uuid
from dataclasses import asdict

from core.agents.prompts import _DOCTOR, _PATIENT
from core.config.doctor_distribution import US_BASELINE_DOCTOR
from core.config.patient_distribution import US_ADULT_BASELINE
from core.db.database import Database
from core.db.queries.optimization_targets import create_optimization_target
from core.types import (
    DoctorDistribution,
    ExperimentRecord,
    PatientDistribution,
)


def _exp(row) -> ExperimentRecord | None:
    if row is None:
        return None
    return ExperimentRecord(
        id=row["id"],
        name=row["name"],
        created_at=row["created_at"],
        patient_distribution=PatientDistribution.from_dict(json.loads(row["patient_distribution_json"])),
        doctor_distribution=DoctorDistribution.from_dict(json.loads(row["doctor_distribution_json"])),
        current_optimization_target_id=row["current_optimization_target_id"],
    )


def create_experiment(
    db: Database,
    name: str,
    patient_distribution: PatientDistribution = US_ADULT_BASELINE,
    doctor_distribution: DoctorDistribution = US_BASELINE_DOCTOR,
) -> ExperimentRecord:
    exp_id = str(uuid.uuid4())
    db.execute(
        """INSERT INTO experiments (id, name, patient_distribution_json, doctor_distribution_json)
           VALUES (?, ?, ?, ?)""",
        (
            exp_id,
            name,
            json.dumps(asdict(patient_distribution)),
            json.dumps(asdict(doctor_distribution)),
        ),
    )
    # Seed the initial optimization target with the current default prompts.
    initial_target = create_optimization_target(
        db,
        experiment_id=exp_id,
        kind="doctor_and_patient",
        prompts={"doctor": _DOCTOR, "patient": _PATIENT},
        parent_id=None,
    )
    db.execute(
        "UPDATE experiments SET current_optimization_target_id = ? WHERE id = ?",
        (initial_target.id, exp_id),
    )
    return _exp(db.conn.execute("SELECT * FROM experiments WHERE id = ?", (exp_id,)).fetchone())


def set_current_optimization_target(db: Database, exp_id: str, target_id: str) -> None:
    db.execute(
        "UPDATE experiments SET current_optimization_target_id = ? WHERE id = ?",
        (target_id, exp_id),
    )


def get_experiment(db: Database, exp_id: str) -> ExperimentRecord | None:
    return _exp(db.conn.execute("SELECT * FROM experiments WHERE id = ?", (exp_id,)).fetchone())


def list_experiments(db: Database) -> list[ExperimentRecord]:
    rows = db.conn.execute(
        "SELECT * FROM experiments ORDER BY created_at DESC, rowid DESC"
    ).fetchall()
    return [_exp(r) for r in rows]


def delete_experiment(db: Database, exp_id: str) -> None:
    # Mirror delete_simulation's explicit cascade pattern.
    sim_ids = [
        r["id"]
        for r in db.conn.execute(
            "SELECT id FROM simulations WHERE experiment_id = ?", (exp_id,)
        ).fetchall()
    ]
    for sid in sim_ids:
        db.execute("DELETE FROM simulation_turns WHERE simulation_id = ?", (sid,))
        db.execute("DELETE FROM evaluations WHERE simulation_id = ?", (sid,))
    db.execute("DELETE FROM simulations WHERE experiment_id = ?", (exp_id,))
    db.execute("DELETE FROM experiments WHERE id = ?", (exp_id,))
