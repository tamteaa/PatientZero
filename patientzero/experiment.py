"""
Experiment — user-facing facade.

    exp = Experiment(config)                          # in-memory
    exp = Experiment(config, db=Database("data.db"))  # persistent
    await exp.run(n=5)
"""

from __future__ import annotations

import asyncio
from statistics import mean

from patientzero.analysis.coverage import compute_coverage
from patientzero.judge import Judge
from patientzero.llm.factory import parse_provider_model
from patientzero.db.database import Database
from patientzero.repositories import RepoSet
from patientzero.services.feedback import FeedbackService
from patientzero.logger import SimulationLogger
from patientzero.simulation import Simulation
from patientzero.types import (
    ExperimentConfig,
    ExperimentRecord,
    JudgeConfig,
    Message,
    Transcript,
)


class Experiment:
    """Facade bundling an ExperimentRecord, its RepoSet, and a SimulationService."""

    def __init__(
        self,
        config: ExperimentConfig,
        db: Database = None,
    ):
        if db is None:
            db = Database(":memory:")
            db.init()
        repos = RepoSet.for_db(db)
        self._repos = repos
        self._logger = SimulationLogger()
        if repos.experiments.get_by_name(config.name) is not None:
            raise ValueError(f"Experiment {config.name!r} already exists")
        with repos.experiments.transaction():
            record = repos.experiments.create(config)
            target = repos.optimization_targets.seed_initial(
                record.id,
                {agent.name: agent.prompt for agent in config.agents},
            )
            repos.experiments.set_current_optimization_target(record.id, target.id)
        refreshed = repos.experiments.get(record.id)
        assert refreshed is not None
        self._record: ExperimentRecord = refreshed

    @classmethod
    def load(cls, name: str, db: Database = None) -> "Experiment":
        if db is None:
            db = Database(":memory:")
            db.init()
        repos = RepoSet.for_db(db)
        record = repos.experiments.get_by_name(name)
        if record is None:
            raise ValueError(f"Experiment {name!r} not found")
        self = cls.__new__(cls)
        self._repos = repos
        self._logger = SimulationLogger()
        self._record = record
        return self

    # ── Accessors ───────────────────────────────────────────────────────────

    @property
    def record(self) -> ExperimentRecord:
        refreshed = self._repos.experiments.get(self._record.id)
        if refreshed is not None:
            self._record = refreshed
        return self._record

    @property
    def config(self) -> ExperimentConfig:
        return self.record.config

    @property
    def id(self) -> str:
        return self._record.id

    def _judge(self) -> Judge:
        jc: JudgeConfig = self.config.judge
        return Judge(rubric=dict(jc.rubric), instructions=jc.instructions, model=jc.model)

    # ── Run ─────────────────────────────────────────────────────────────────

    async def run(
        self,
        n: int,
        where: dict[str, dict[str, str]] | None = None,
        concurrency: int = 4,
    ) -> list[str]:
        if n < 1:
            return []
        where = where or {}
        semaphore = asyncio.Semaphore(concurrency)
        sim_ids: list[str] = []
        judge = self._judge()
        judge_model = judge.model or self.config.model

        async def run_one() -> None:
            async with semaphore:
                record = self.record
                sample_rng = self._repos.experiments.acquire_next_sample_rng(record.id)
                profiles = {
                    agent.name: agent.sample(
                        rng=sample_rng,
                        **where.get(agent.name, {}),
                    )
                    for agent in record.config.agents
                }
                sim = Simulation.create(record, profiles, self._repos, logger=self._logger)
                sim_ids.append(sim.sim_id)
                await sim.run()
                turns = self._repos.simulations.get_turns(sim.sim_id)
                transcript = Transcript(
                    messages=[Message(role=t.role, content=t.content) for t in turns]
                )
                provider, model_name = parse_provider_model(judge_model)
                result = await judge.bind(provider, model_name).evaluate(transcript)
                self._logger.log_evaluation(sim.sim_id, result)
                self._repos.evaluations.delete_for_simulation(sim.sim_id)
                self._repos.evaluations.create_or_append(
                    simulation_id=sim.sim_id,
                    experiment_id=record.id,
                    judge_result=result,
                )
                final = self._repos.simulations.get(sim.sim_id)
                self._logger.close(
                    sim.sim_id,
                    state=final.state if final else "error",
                    duration_ms=final.duration_ms or 0.0 if final else 0.0,
                )

        await asyncio.gather(*(run_one() for _ in range(n)))
        return sim_ids

    # ── Optimize / analyze / inspect ────────────────────────────────────────

    async def optimize(self):
        return await FeedbackService(self._repos).optimize(self.record.id)

    def coverage(self, samples: int = 100_000):
        sims = self._repos.simulations.list_for_experiment(self.record.id)
        return compute_coverage(sims, self.config.agents, samples=samples)

    def scores(self, optimization_target_id: str | None = None) -> dict[str, float]:
        evals = self._repos.evaluations.list_for_experiment(self.record.id)
        if optimization_target_id is not None:
            sim_ids = {
                sim.id
                for sim in self._repos.simulations.list_for_experiment(self.record.id)
                if sim.config.optimization_target_id == optimization_target_id
            }
            evals = [e for e in evals if e.simulation_id in sim_ids]
        buckets: dict[str, list[float]] = {}
        for ev in evals:
            for result in ev.judge_results:
                for name, value in result.scores.items():
                    if value is not None:
                        buckets.setdefault(name, []).append(value)
        return {name: mean(values) for name, values in buckets.items()}

    def simulations(self, optimization_target: str | None = None):
        sims = self._repos.simulations.list_for_experiment(self.record.id)
        if optimization_target is None:
            return sims
        return [sim for sim in sims if sim.config.optimization_target_id == optimization_target]

    def history(self):
        return self._repos.optimization_targets.list_for_experiment(self.record.id)
