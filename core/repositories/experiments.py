"""
ExperimentRepository — owns the `experiments` table.

Experiments are the top-level aggregate; simulations, evaluations, and
optimization targets all roll up to one. Cross-aggregate orchestration
(e.g. "create an experiment AND seed its first optimization target")
belongs in the service/facade layer, not here.
"""
from __future__ import annotations

import json
import uuid

from core.repositories.base import BaseRepository
from core.sampling import stable_rng
from core.types import ExperimentConfig, ExperimentRecord


_EMPTY_COUNTS = {"total": 0, "completed": 0, "running": 0, "error": 0, "evaluated": 0}


class ExperimentRepository(BaseRepository):
    TABLE = "experiments"

    # ── Row hydration ───────────────────────────────────────────────────────

    def _hydrate(self, row) -> ExperimentRecord | None:
        if row is None:
            return None
        r = dict(row)
        return ExperimentRecord(
            id=r["id"],
            created_at=r["created_at"],
            config=ExperimentConfig.from_dict(json.loads(r["config_json"])),
            current_optimization_target_id=r["current_optimization_target_id"],
            sample_draw_index=int(r.get("sample_draw_index") or 0),
        )

    # ── Reads ───────────────────────────────────────────────────────────────

    def get(self, experiment_id: str) -> ExperimentRecord | None:
        row = self.db.conn.execute(
            "SELECT * FROM experiments WHERE id = ?", (experiment_id,)
        ).fetchone()
        return self._hydrate(row)

    def get_by_name(self, name: str) -> ExperimentRecord | None:
        rows = self.db.conn.execute("SELECT * FROM experiments").fetchall()
        for row in rows:
            record = self._hydrate(row)
            if record is not None and record.config.name == name:
                return record
        return None

    def list_all(self) -> list[ExperimentRecord]:
        rows = self.db.conn.execute(
            "SELECT * FROM experiments ORDER BY created_at DESC, rowid DESC"
        ).fetchall()
        return [r for r in (self._hydrate(row) for row in rows) if r is not None]

    def counts_for(self, experiment_id: str) -> dict:
        rows = self.db.conn.execute(
            """SELECT state, COUNT(*) AS n
                 FROM simulations
                WHERE experiment_id = ?
             GROUP BY state""",
            (experiment_id,),
        ).fetchall()
        by_state = {r["state"]: r["n"] for r in rows}
        evaluated = self.db.conn.execute(
            "SELECT COUNT(*) FROM evaluations WHERE experiment_id = ?",
            (experiment_id,),
        ).fetchone()[0]
        return {
            "total": sum(by_state.values()),
            "completed": by_state.get("completed", 0),
            "running": by_state.get("running", 0),
            "error": by_state.get("error", 0),
            "evaluated": evaluated,
        }

    def counts_all(self) -> dict[str, dict]:
        sim_rows = self.db.conn.execute(
            """SELECT experiment_id, state, COUNT(*) AS n
                 FROM simulations
             GROUP BY experiment_id, state"""
        ).fetchall()
        eval_rows = self.db.conn.execute(
            """SELECT experiment_id, COUNT(*) AS n
                 FROM evaluations
                WHERE experiment_id IS NOT NULL
             GROUP BY experiment_id"""
        ).fetchall()
        out: dict[str, dict] = {}
        for r in sim_rows:
            d = out.setdefault(r["experiment_id"], dict(_EMPTY_COUNTS))
            d[r["state"]] = r["n"]
            d["total"] += r["n"]
        for r in eval_rows:
            d = out.setdefault(r["experiment_id"], dict(_EMPTY_COUNTS))
            d["evaluated"] = r["n"]
        return out

    # ── Writes ──────────────────────────────────────────────────────────────

    def create(self, config: ExperimentConfig) -> ExperimentRecord:
        exp_id = str(uuid.uuid4())
        self.db.execute(
            "INSERT INTO experiments (id, config_json) VALUES (?, ?)",
            (exp_id, json.dumps(config.to_dict())),
        )
        created = self.get(exp_id)
        assert created is not None
        return created

    def set_current_optimization_target(self, experiment_id: str, target_id: str) -> None:
        self.db.execute(
            "UPDATE experiments SET current_optimization_target_id = ? WHERE id = ?",
            (target_id, experiment_id),
        )

    def reset_sample_draw_index(self, experiment_id: str) -> None:
        self.db.execute(
            "UPDATE experiments SET sample_draw_index = 0 WHERE id = ?",
            (experiment_id,),
        )

    def acquire_next_sample_rng(self, experiment_id: str):
        """
        If the experiment's config has a seed, return a deterministic RNG for
        the next draw and atomically increment ``sample_draw_index``. Returns
        ``None`` if the experiment has no seed. Uses BEGIN IMMEDIATE so
        concurrent sim starts cannot reuse the same index.
        """
        self.db.conn.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.conn.execute(
                "SELECT config_json, sample_draw_index FROM experiments WHERE id = ?",
                (experiment_id,),
            ).fetchone()
            if not row:
                self.db.conn.rollback()
                return None
            config = ExperimentConfig.from_dict(json.loads(row["config_json"]))
            if config.seed is None:
                self.db.conn.rollback()
                return None
            idx = int(row["sample_draw_index"])
            self.db.conn.execute(
                "UPDATE experiments SET sample_draw_index = sample_draw_index + 1 WHERE id = ?",
                (experiment_id,),
            )
            self.db.conn.commit()
            return stable_rng(config.seed, idx)
        except Exception:
            self.db.conn.rollback()
            raise

    def delete(self, experiment_id: str) -> None:
        sim_ids = [
            r["id"]
            for r in self.db.conn.execute(
                "SELECT id FROM simulations WHERE experiment_id = ?", (experiment_id,)
            ).fetchall()
        ]
        with self.transaction():
            for sid in sim_ids:
                self.db.conn.execute(
                    "DELETE FROM simulation_turns WHERE simulation_id = ?", (sid,)
                )
                self.db.conn.execute(
                    "DELETE FROM evaluations WHERE simulation_id = ?", (sid,)
                )
            self.db.conn.execute(
                "DELETE FROM simulations WHERE experiment_id = ?", (experiment_id,)
            )
            self.db.conn.execute(
                "DELETE FROM optimization_targets WHERE experiment_id = ?", (experiment_id,)
            )
            self.db.conn.execute(
                "DELETE FROM experiments WHERE id = ?", (experiment_id,)
            )
