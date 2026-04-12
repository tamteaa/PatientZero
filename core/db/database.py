import sqlite3
from pathlib import Path


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def init(self):
        schema_path = Path(__file__).parent / "schema.sql"
        self.conn.executescript(schema_path.read_text())
        self.conn.commit()

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        cursor = self.conn.execute(query, params)
        self.conn.commit()
        return cursor

    def fetch_one(self, query: str, params: tuple = ()) -> dict | None:
        row = self.conn.execute(query, params).fetchone()
        return dict(row) if row else None

    def fetch_all(self, query: str, params: tuple = ()) -> list[dict]:
        rows = self.conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
