import uuid
from core.db.database import Database
from core.types import SessionRecord, TurnRecord


def _session(row) -> SessionRecord | None:
    return SessionRecord(**dict(row)) if row else None


def _turn(row) -> TurnRecord:
    return TurnRecord(**dict(row))


def create_session(db: Database, model: str = "mock:default") -> SessionRecord:
    session_id = str(uuid.uuid4())
    db.execute("INSERT INTO sessions (id, model) VALUES (?, ?)", (session_id, model))
    return _session(db.conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone())


def get_session(db: Database, session_id: str) -> SessionRecord | None:
    return _session(db.conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone())


def list_sessions(db: Database) -> list[SessionRecord]:
    rows = db.conn.execute("SELECT * FROM sessions ORDER BY created_at DESC, rowid DESC").fetchall()
    return [SessionRecord(**dict(r)) for r in rows]


def update_session_title(db: Database, session_id: str, title: str):
    db.execute("UPDATE sessions SET title = ? WHERE id = ?", (title, session_id))


def update_session_model(db: Database, session_id: str, model: str):
    db.execute("UPDATE sessions SET model = ? WHERE id = ?", (model, session_id))


def delete_session(db: Database, session_id: str):
    db.execute("DELETE FROM turns WHERE session_id = ?", (session_id,))
    db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))


def create_turn(db: Database, session_id: str, role: str, content: str, turn_number: int):
    db.execute(
        "INSERT INTO turns (session_id, role, content, turn_number) VALUES (?, ?, ?, ?)",
        (session_id, role, content, turn_number),
    )


def get_turns(db: Database, session_id: str) -> list[TurnRecord]:
    rows = db.conn.execute(
        "SELECT * FROM turns WHERE session_id = ? ORDER BY turn_number",
        (session_id,),
    ).fetchall()
    return [_turn(r) for r in rows]


def get_turn_count(db: Database, session_id: str) -> int:
    row = db.conn.execute(
        "SELECT COUNT(*) as count FROM turns WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    return row["count"] if row else 0
