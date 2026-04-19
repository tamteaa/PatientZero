from __future__ import annotations

import sqlite3
from contextlib import asynccontextmanager
from importlib import resources

import aiosqlite


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> aiosqlite.Connection:
        if self._conn is None:
            self._conn = await aiosqlite.connect(self.db_path, isolation_level=None)
            self._conn.row_factory = sqlite3.Row
            await self._conn.execute("PRAGMA journal_mode=WAL")
            await self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError(
                "Database.connect() must be awaited before accessing .conn"
            )
        return self._conn

    async def init(self) -> None:
        await self.connect()
        schema = resources.files("patientzero.db").joinpath("schema.sql").read_text()
        await self._conn.executescript(schema)
        await self._conn.commit()

    async def execute(self, query: str, params: tuple = ()) -> aiosqlite.Cursor:
        cursor = await self.conn.execute(query, params)
        await self.conn.commit()
        return cursor

    async def fetch_one(self, query: str, params: tuple = ()) -> dict | None:
        async with self.conn.execute(query, params) as cur:
            row = await cur.fetchone()
        return dict(row) if row else None

    async def fetch_all(self, query: str, params: tuple = ()) -> list[dict]:
        async with self.conn.execute(query, params) as cur:
            rows = await cur.fetchall()
        return [dict(row) for row in rows]

    @asynccontextmanager
    async def transaction(self):
        """
        Atomic multi-statement write. aiosqlite autocommits by default
        unless we explicitly open a transaction — BEGIN here mirrors the
        old `with db.conn:` semantics.
        """
        await self.conn.execute("BEGIN")
        try:
            yield
            await self.conn.commit()
        except Exception:
            await self.conn.rollback()
            raise

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
