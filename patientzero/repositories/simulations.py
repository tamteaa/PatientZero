"""
SimulationRepository — owns the `simulations` and `simulation_turns` tables.
"""
from __future__ import annotations

import json
import uuid

from patientzero.repositories.base import BaseRepository
from patientzero.types import SimulationConfig, SimulationRecord, SimulationTurnRecord


class SimulationRepository(BaseRepository):
    TABLE = "simulations"

    # ── Row hydration ───────────────────────────────────────────────────────

    def _hydrate(self, row) -> SimulationRecord | None:
        if row is None:
            return None
        r = dict(row)
        return SimulationRecord(
            id=r["id"],
            created_at=r["created_at"],
            config=SimulationConfig.from_dict(json.loads(r["config_json"])),
            state=r["state"],
            duration_ms=r["duration_ms"],
            completed_at=r["completed_at"],
        )

    def _hydrate_turn(self, row) -> SimulationTurnRecord:
        return SimulationTurnRecord(**dict(row))

    # ── Reads ───────────────────────────────────────────────────────────────

    async def get(self, simulation_id: str) -> SimulationRecord | None:
        async with self.db.conn.execute(
            "SELECT * FROM simulations WHERE id = ?", (simulation_id,)
        ) as cur:
            row = await cur.fetchone()
        return self._hydrate(row)

    async def list_for_experiment(self, experiment_id: str) -> list[SimulationRecord]:
        async with self.db.conn.execute(
            """SELECT * FROM simulations
                WHERE experiment_id = ?
             ORDER BY created_at DESC, rowid DESC""",
            (experiment_id,),
        ) as cur:
            rows = await cur.fetchall()
        return [r for r in (self._hydrate(row) for row in rows) if r is not None]

    async def get_turns(self, simulation_id: str) -> list[SimulationTurnRecord]:
        async with self.db.conn.execute(
            "SELECT * FROM simulation_turns WHERE simulation_id = ? ORDER BY turn_number",
            (simulation_id,),
        ) as cur:
            rows = await cur.fetchall()
        return [self._hydrate_turn(r) for r in rows]

    # ── Writes ──────────────────────────────────────────────────────────────

    async def create(self, config: SimulationConfig) -> SimulationRecord:
        sim_id = str(uuid.uuid4())
        await self.db.execute(
            """INSERT INTO simulations
                 (id, experiment_id, optimization_target_id, config_json)
               VALUES (?, ?, ?, ?)""",
            (
                sim_id,
                config.experiment_id,
                config.optimization_target_id,
                json.dumps(config.to_dict()),
            ),
        )
        created = await self.get(sim_id)
        assert created is not None
        return created

    async def complete(self, simulation_id: str, duration_ms: float) -> None:
        await self.db.execute(
            """UPDATE simulations
                  SET state = 'completed', duration_ms = ?, completed_at = datetime('now')
                WHERE id = ?""",
            (duration_ms, simulation_id),
        )

    async def fail(self, simulation_id: str) -> None:
        await self.db.execute(
            "UPDATE simulations SET state = 'error' WHERE id = ?",
            (simulation_id,),
        )

    async def add_turn(
        self,
        simulation_id: str,
        turn_number: int,
        role: str,
        agent_type: str,
        content: str,
        duration_ms: float,
    ) -> None:
        await self.db.execute(
            """INSERT INTO simulation_turns
                 (simulation_id, turn_number, role, agent_type, content, duration_ms)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (simulation_id, turn_number, role, agent_type, content, duration_ms),
        )

    async def delete(self, simulation_id: str) -> None:
        async with self.transaction():
            await self.db.conn.execute(
                "DELETE FROM simulation_turns WHERE simulation_id = ?", (simulation_id,)
            )
            await self.db.conn.execute(
                "DELETE FROM evaluations WHERE simulation_id = ?", (simulation_id,)
            )
            await self.db.conn.execute(
                "DELETE FROM simulations WHERE id = ?", (simulation_id,)
            )
