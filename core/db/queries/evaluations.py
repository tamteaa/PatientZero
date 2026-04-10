import json

from core.db.database import Database
from core.types import EvaluationRecord, JudgeResult


def _row_to_record(row) -> EvaluationRecord | None:
    if not row:
        return None
    data = dict(row)
    judge_results = [
        JudgeResult.from_dict(j) for j in json.loads(data["judge_results_json"])
    ]
    return EvaluationRecord(
        id=data["id"],
        simulation_id=data["simulation_id"],
        created_at=data["created_at"],
        judge_results=judge_results,
    )


def create_evaluation(
    db: Database,
    simulation_id: str,
    judge_result: JudgeResult,
) -> EvaluationRecord:
    existing = get_evaluation(db, simulation_id)
    results = existing.judge_results if existing else []
    results.append(judge_result)
    blob = json.dumps([j.to_dict() for j in results])

    if existing:
        db.execute(
            "UPDATE evaluations SET judge_results_json = ? WHERE id = ?",
            (blob, existing.id),
        )
    else:
        db.execute(
            "INSERT INTO evaluations (simulation_id, judge_results_json) VALUES (?, ?)",
            (simulation_id, blob),
        )
    return get_evaluation(db, simulation_id)


def get_evaluation(db: Database, simulation_id: str) -> EvaluationRecord | None:
    return _row_to_record(
        db.conn.execute(
            "SELECT * FROM evaluations WHERE simulation_id = ? ORDER BY id DESC LIMIT 1",
            (simulation_id,),
        ).fetchone()
    )


def list_evaluations(db: Database) -> list[EvaluationRecord]:
    rows = db.conn.execute(
        "SELECT * FROM evaluations ORDER BY created_at DESC",
    ).fetchall()
    return [r for r in (_row_to_record(row) for row in rows) if r]


def delete_evaluation(db: Database, simulation_id: str) -> None:
    db.execute("DELETE FROM evaluations WHERE simulation_id = ?", (simulation_id,))
