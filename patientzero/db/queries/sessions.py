"""
Legacy — chat route (/api/chat, /api/sessions) only. Do not migrate to
`core/repositories/` without reviewing the chat path; the session/turn
model predates experiments and has different lifecycle semantics.
"""
from __future__ import annotations

import uuid
from patientzero.db.database import Database
from patientzero.types import SessionRecord, TurnRecord


def _session(row) -> SessionRecord | None:
    return SessionRecord(**dict(row)) if row else None


def _turn(row) -> TurnRecord:
    return TurnRecord(**dict(row))


async def create_session(db: Database, model: str = "mock:default") -> SessionRecord:
    session_id = str(uuid.uuid4())
    await db.execute("INSERT INTO sessions (id, model) VALUES (?, ?)", (session_id, model))
    async with db.conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)) as cur:
        row = await cur.fetchone()
    return _session(row)


async def get_session(db: Database, session_id: str) -> SessionRecord | None:
    async with db.conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)) as cur:
        row = await cur.fetchone()
    return _session(row)


async def list_sessions(db: Database) -> list[SessionRecord]:
    async with db.conn.execute("SELECT * FROM sessions ORDER BY created_at DESC, rowid DESC") as cur:
        rows = await cur.fetchall()
    return [SessionRecord(**dict(r)) for r in rows]


async def update_session_title(db: Database, session_id: str, title: str):
    await db.execute("UPDATE sessions SET title = ? WHERE id = ?", (title, session_id))


async def update_session_model(db: Database, session_id: str, model: str):
    await db.execute("UPDATE sessions SET model = ? WHERE id = ?", (model, session_id))


async def delete_session(db: Database, session_id: str):
    await db.execute("DELETE FROM turns WHERE session_id = ?", (session_id,))
    await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))


async def create_turn(db: Database, session_id: str, role: str, content: str, turn_number: int):
    await db.execute(
        "INSERT INTO turns (session_id, role, content, turn_number) VALUES (?, ?, ?, ?)",
        (session_id, role, content, turn_number),
    )


async def get_turns(db: Database, session_id: str) -> list[TurnRecord]:
    async with db.conn.execute(
        "SELECT * FROM turns WHERE session_id = ? ORDER BY turn_number",
        (session_id,),
    ) as cur:
        rows = await cur.fetchall()
    return [_turn(r) for r in rows]


async def get_turn_count(db: Database, session_id: str) -> int:
    async with db.conn.execute(
        "SELECT COUNT(*) as count FROM turns WHERE session_id = ?",
        (session_id,),
    ) as cur:
        row = await cur.fetchone()
    return row["count"] if row else 0
