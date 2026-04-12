"""
EvaluationRepository — owns the `evaluations` table.
"""
from __future__ import annotations

import json

from patientzero.repositories.base import BaseRepository
from patientzero.repositories.simulations import SimulationRepository
from patientzero.types import EvaluationRecord, JudgeResult, SimulationConfig, SimulationRecord


class EvaluationRepository(BaseRepository):
    TABLE = "evaluations"

    def _hydrate(self, row) -> EvaluationRecord | None:
        if not row:
            return None
        data = dict(row)
        return EvaluationRecord(
            id=data["id"],
            simulation_id=data["simulation_id"],
            experiment_id=data.get("experiment_id"),
            created_at=data["created_at"],
            judge_results=[
                JudgeResult.from_dict(j)
                for j in json.loads(data["judge_results_json"])
            ],
        )

    # ── Reads ───────────────────────────────────────────────────────────────

    def get_latest_for_simulation(self, simulation_id: str) -> EvaluationRecord | None:
        row = self.db.conn.execute(
            "SELECT * FROM evaluations WHERE simulation_id = ? ORDER BY id DESC LIMIT 1",
            (simulation_id,),
        ).fetchone()
        return self._hydrate(row)

    def list_for_experiment(self, experiment_id: str) -> list[EvaluationRecord]:
        rows = self.db.conn.execute(
            "SELECT * FROM evaluations WHERE experiment_id = ? ORDER BY created_at DESC",
            (experiment_id,),
        ).fetchall()
        return [r for r in (self._hydrate(row) for row in rows) if r is not None]

    def list_all(self) -> list[EvaluationRecord]:
        rows = self.db.conn.execute(
            "SELECT * FROM evaluations ORDER BY created_at DESC"
        ).fetchall()
        return [r for r in (self._hydrate(row) for row in rows) if r is not None]

    def list_completed_with_evaluations_for_experiment(
        self, experiment_id: str
    ) -> list[tuple[SimulationRecord, EvaluationRecord]]:
        rows = self.db.conn.execute(
            """SELECT s.id               AS sim_id,
                      s.experiment_id    AS sim_experiment_id,
                      s.config_json      AS sim_config_json,
                      s.state            AS sim_state,
                      s.duration_ms      AS sim_duration_ms,
                      s.created_at       AS sim_created_at,
                      s.completed_at     AS sim_completed_at,
                      e.id                 AS eval_id,
                      e.simulation_id      AS eval_sim_id,
                      e.experiment_id      AS eval_experiment_id,
                      e.judge_results_json AS eval_judge_results_json,
                      e.created_at         AS eval_created_at
                 FROM simulations s
                 JOIN evaluations e ON e.simulation_id = s.id
                WHERE s.experiment_id = ?
                  AND s.state = 'completed'
             ORDER BY e.created_at DESC""",
            (experiment_id,),
        ).fetchall()
        pairs: list[tuple[SimulationRecord, EvaluationRecord]] = []
        for r in rows:
            d = dict(r)
            sim = SimulationRecord(
                id=d["sim_id"],
                created_at=d["sim_created_at"],
                config=SimulationConfig.from_dict(json.loads(d["sim_config_json"])),
                state=d["sim_state"],
                duration_ms=d["sim_duration_ms"],
                completed_at=d["sim_completed_at"],
            )
            ev = EvaluationRecord(
                id=d["eval_id"],
                simulation_id=d["eval_sim_id"],
                experiment_id=d["eval_experiment_id"],
                created_at=d["eval_created_at"],
                judge_results=[
                    JudgeResult.from_dict(j)
                    for j in json.loads(d["eval_judge_results_json"])
                ],
            )
            pairs.append((sim, ev))
        return pairs

    # ── Writes ──────────────────────────────────────────────────────────────

    def create_or_append(
        self,
        simulation_id: str,
        experiment_id: str,
        judge_result: JudgeResult,
    ) -> EvaluationRecord:
        existing = self.get_latest_for_simulation(simulation_id)
        results = existing.judge_results if existing else []
        results.append(judge_result)
        blob = json.dumps([j.to_dict() for j in results])

        if existing:
            self.db.execute(
                "UPDATE evaluations SET judge_results_json = ? WHERE id = ?",
                (blob, existing.id),
            )
        else:
            self.db.execute(
                """INSERT INTO evaluations (simulation_id, experiment_id, judge_results_json)
                   VALUES (?, ?, ?)""",
                (simulation_id, experiment_id, blob),
            )
        result = self.get_latest_for_simulation(simulation_id)
        assert result is not None
        return result

    def delete_for_simulation(self, simulation_id: str) -> None:
        self.db.execute(
            "DELETE FROM evaluations WHERE simulation_id = ?", (simulation_id,)
        )
