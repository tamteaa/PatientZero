from core.db.database import Database
from core.types import EvaluationRecord


def _eval(row) -> EvaluationRecord | None:
    return EvaluationRecord(**dict(row)) if row else None


def create_evaluation(
    db: Database,
    simulation_id: str,
    model: str,
    result: dict,
) -> EvaluationRecord:
    db.execute(
        """INSERT INTO evaluations (
            simulation_id, model,
            comprehension_score, factual_recall, applied_reasoning,
            explanation_quality, interaction_quality,
            confidence_comprehension_gap, justification
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            simulation_id,
            model,
            result.get("comprehension_score"),
            result.get("factual_recall"),
            result.get("applied_reasoning"),
            result.get("explanation_quality"),
            result.get("interaction_quality"),
            result.get("confidence_comprehension_gap"),
            result.get("justification"),
        ),
    )
    return _eval(
        db.conn.execute(
            "SELECT * FROM evaluations WHERE simulation_id = ? ORDER BY id DESC LIMIT 1",
            (simulation_id,),
        ).fetchone()
    )


def get_evaluation(db: Database, simulation_id: str) -> EvaluationRecord | None:
    return _eval(
        db.conn.execute(
            "SELECT * FROM evaluations WHERE simulation_id = ? ORDER BY id DESC LIMIT 1",
            (simulation_id,),
        ).fetchone()
    )


def list_evaluations(db: Database) -> list[EvaluationRecord]:
    rows = db.conn.execute(
        """SELECT e.*, s.persona_name, s.scenario_name
           FROM evaluations e
           JOIN simulations s ON s.id = e.simulation_id
           ORDER BY e.created_at DESC""",
    ).fetchall()
    return [EvaluationRecord(**dict(r)) for r in rows]


def delete_evaluation(db: Database, simulation_id: str) -> None:
    db.execute("DELETE FROM evaluations WHERE simulation_id = ?", (simulation_id,))
