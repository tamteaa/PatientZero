from core.db.database import Database


def create_evaluation(
    db: Database,
    simulation_id: str,
    model: str,
    result: dict,
) -> dict:
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
    return db.fetch_one(
        "SELECT * FROM evaluations WHERE simulation_id = ? ORDER BY id DESC LIMIT 1",
        (simulation_id,),
    )


def get_evaluation(db: Database, simulation_id: str) -> dict | None:
    return db.fetch_one(
        "SELECT * FROM evaluations WHERE simulation_id = ? ORDER BY id DESC LIMIT 1",
        (simulation_id,),
    )


def list_evaluations(db: Database) -> list[dict]:
    return db.fetch_all(
        """SELECT e.*, s.persona_name, s.scenario_name, s.style, s.mode
           FROM evaluations e
           JOIN simulations s ON s.id = e.simulation_id
           ORDER BY e.created_at DESC""",
    )


def delete_evaluation(db: Database, simulation_id: str) -> None:
    db.execute("DELETE FROM evaluations WHERE simulation_id = ?", (simulation_id,))