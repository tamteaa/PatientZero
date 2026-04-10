import json
import uuid
from dataclasses import asdict

from core.config.doctor_distribution import US_BASELINE_DOCTOR
from core.config.patient_distribution import US_ADULT_BASELINE
from core.db.database import Database
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
    return _exp(db.conn.execute("SELECT * FROM experiments WHERE id = ?", (exp_id,)).fetchone())


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
