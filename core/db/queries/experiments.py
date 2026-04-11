import json
import uuid
from dataclasses import asdict

from core.agents.prompts import _DOCTOR, _PATIENT
from core.config.doctor_distribution import US_BASELINE_DOCTOR
from core.config.patient_distribution import US_ADULT_BASELINE
from core.db.database import Database
from core.db.queries.optimization_targets import create_optimization_target
from core.sampling import stable_rng
from core.types import (
    DoctorDistribution,
    ExperimentRecord,
    PatientDistribution,
)


def _exp(row) -> ExperimentRecord | None:
    if row is None:
        return None
    r = dict(row)
    return ExperimentRecord(
        id=r["id"],
        name=r["name"],
        created_at=r["created_at"],
        patient_distribution=PatientDistribution.from_dict(json.loads(r["patient_distribution_json"])),
        doctor_distribution=DoctorDistribution.from_dict(json.loads(r["doctor_distribution_json"])),
        current_optimization_target_id=r["current_optimization_target_id"],
        sampling_seed=r.get("sampling_seed"),
        sample_draw_index=int(r.get("sample_draw_index") or 0),
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


def acquire_next_sample_rng(db: Database, exp_id: str):
    """
    If the experiment has ``sampling_seed``, return a deterministic RNG for the next draw
    and increment ``sample_draw_index``. Otherwise return ``None``.
    Uses a single transaction so concurrent sim starts do not reuse the same index.
    """
    db.conn.execute("BEGIN IMMEDIATE")
    try:
        row = db.conn.execute(
            "SELECT sampling_seed, sample_draw_index FROM experiments WHERE id = ?", (exp_id,)
        ).fetchone()
        if not row or row["sampling_seed"] is None:
            db.conn.rollback()
            return None
        seed, idx = int(row["sampling_seed"]), int(row["sample_draw_index"])
        db.conn.execute(
            "UPDATE experiments SET sample_draw_index = sample_draw_index + 1 WHERE id = ?",
            (exp_id,),
        )
        db.conn.commit()
        return stable_rng(seed, idx)
    except Exception:
        db.conn.rollback()
        raise


def set_experiment_sampling_seed(db: Database, exp_id: str, sampling_seed: int | None) -> None:
    db.execute(
        "UPDATE experiments SET sampling_seed = ? WHERE id = ?",
        (sampling_seed, exp_id),
    )


def reset_experiment_sample_draw_index(db: Database, exp_id: str) -> None:
    db.execute("UPDATE experiments SET sample_draw_index = 0 WHERE id = ?", (exp_id,))


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
