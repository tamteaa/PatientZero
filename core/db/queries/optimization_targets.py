import json
import uuid

from core.db.database import Database
from core.types import OptimizationTarget


def _target(row) -> OptimizationTarget | None:
    if row is None:
        return None
    return OptimizationTarget(
        id=row["id"],
        experiment_id=row["experiment_id"],
        kind=row["kind"],
        prompts=json.loads(row["prompts_json"]),
        parent_id=row["parent_id"],
        created_at=row["created_at"],
    )


def create_optimization_target(
    db: Database,
    experiment_id: str,
    kind: str,
    prompts: dict[str, str],
    parent_id: str | None = None,
) -> OptimizationTarget:
    target_id = str(uuid.uuid4())
    db.execute(
        """INSERT INTO optimization_targets (id, experiment_id, kind, prompts_json, parent_id)
           VALUES (?, ?, ?, ?, ?)""",
        (target_id, experiment_id, kind, json.dumps(prompts), parent_id),
    )
    return _target(
        db.conn.execute(
            "SELECT * FROM optimization_targets WHERE id = ?", (target_id,)
        ).fetchone()
    )


def get_optimization_target(db: Database, target_id: str) -> OptimizationTarget | None:
    return _target(
        db.conn.execute(
            "SELECT * FROM optimization_targets WHERE id = ?", (target_id,)
        ).fetchone()
    )


def list_optimization_targets(db: Database, experiment_id: str) -> list[OptimizationTarget]:
    rows = db.conn.execute(
        "SELECT * FROM optimization_targets WHERE experiment_id = ? ORDER BY created_at DESC, rowid DESC",
        (experiment_id,),
    ).fetchall()
    return [_target(r) for r in rows]
