import uuid
from db.database import Database


def create_session(db: Database, model: str = "mock:default") -> dict:
    session_id = str(uuid.uuid4())
    db.execute("INSERT INTO sessions (id, model) VALUES (?, ?)", (session_id, model))
    return db.fetch_one("SELECT * FROM sessions WHERE id = ?", (session_id,))


def get_session(db: Database, session_id: str) -> dict | None:
    return db.fetch_one("SELECT * FROM sessions WHERE id = ?", (session_id,))


def list_sessions(db: Database) -> list[dict]:
    return db.fetch_all("SELECT * FROM sessions ORDER BY created_at DESC, rowid DESC")


def update_session_title(db: Database, session_id: str, title: str):
    db.execute("UPDATE sessions SET title = ? WHERE id = ?", (title, session_id))


def update_session_model(db: Database, session_id: str, model: str):
    db.execute("UPDATE sessions SET model = ? WHERE id = ?", (model, session_id))


def create_turn(db: Database, session_id: str, role: str, content: str, turn_number: int):
    db.execute(
        "INSERT INTO turns (session_id, role, content, turn_number) VALUES (?, ?, ?, ?)",
        (session_id, role, content, turn_number),
    )


def get_turns(db: Database, session_id: str) -> list[dict]:
    return db.fetch_all(
        "SELECT * FROM turns WHERE session_id = ? ORDER BY turn_number",
        (session_id,),
    )


def get_turn_count(db: Database, session_id: str) -> int:
    result = db.fetch_one(
        "SELECT COUNT(*) as count FROM turns WHERE session_id = ?",
        (session_id,),
    )
    return result["count"] if result else 0
