"""
OptimizationTargetRepository — owns the `optimization_targets` table.

Optimization targets are versioned prompt sets produced by the feedback
loop. Each row belongs to exactly one experiment and may have a parent
target (forming a lineage).
"""

from __future__ import annotations

import json
import uuid

from patientzero.repositories.base import BaseRepository
from patientzero.types import OptimizationTarget


class OptimizationTargetRepository(BaseRepository):
    TABLE = "optimization_targets"

    # ── Row hydration ───────────────────────────────────────────────────────

    def _hydrate(self, row) -> OptimizationTarget | None:
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

    # ── Reads ───────────────────────────────────────────────────────────────

    async def get(self, target_id: str) -> OptimizationTarget | None:
        async with self.db.conn.execute(
            "SELECT * FROM optimization_targets WHERE id = ?", (target_id,)
        ) as cur:
            row = await cur.fetchone()
        return self._hydrate(row)

    async def list_for_experiment(self, experiment_id: str) -> list[OptimizationTarget]:
        async with self.db.conn.execute(
            """SELECT * FROM optimization_targets
                WHERE experiment_id = ?
             ORDER BY created_at DESC, rowid DESC""",
            (experiment_id,),
        ) as cur:
            rows = await cur.fetchall()
        return [r for r in (self._hydrate(row) for row in rows) if r is not None]

    # ── Writes ──────────────────────────────────────────────────────────────

    async def create(
        self,
        experiment_id: str,
        kind: str,
        prompts: dict[str, str],
        parent_id: str | None = None,
    ) -> OptimizationTarget:
        target_id = str(uuid.uuid4())
        await self.db.execute(
            """INSERT INTO optimization_targets
                 (id, experiment_id, kind, prompts_json, parent_id)
               VALUES (?, ?, ?, ?, ?)""",
            (target_id, experiment_id, kind, json.dumps(prompts), parent_id),
        )
        created = await self.get(target_id)
        assert created is not None
        return created

    async def seed_initial(
        self,
        experiment_id: str,
        prompts: dict[str, str],
        kind: str = "agents",
    ) -> OptimizationTarget:
        return await self.create(
            experiment_id=experiment_id,
            kind=kind,
            prompts=prompts,
            parent_id=None,
        )
