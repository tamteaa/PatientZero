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
        schema = schema_path.read_text()
        self.conn.executescript(schema)
        self._migrate_simulations_optimization_target()
        self._migrate_experiments_sampling()
        self.conn.commit()

    def _migrate_simulations_optimization_target(self) -> None:
        cols = {row[1] for row in self.conn.execute("PRAGMA table_info(simulations)")}
        if "optimization_target_id" not in cols:
            self.conn.execute(
                "ALTER TABLE simulations ADD COLUMN optimization_target_id TEXT "
                "REFERENCES optimization_targets(id)"
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_simulations_optimization_target "
                "ON simulations(optimization_target_id)"
            )

    def _migrate_experiments_sampling(self) -> None:
        cols = {row[1] for row in self.conn.execute("PRAGMA table_info(experiments)")}
        if "sampling_seed" not in cols:
            self.conn.execute("ALTER TABLE experiments ADD COLUMN sampling_seed INTEGER")
        if "sample_draw_index" not in cols:
            self.conn.execute(
                "ALTER TABLE experiments ADD COLUMN sample_draw_index INTEGER NOT NULL DEFAULT 0"
            )

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
