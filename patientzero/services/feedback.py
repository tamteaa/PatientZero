"""
FeedbackService — orchestrates one feedback loop run.

Loads every completed simulation for an experiment along with its
evaluation, bundles them as ``FeedbackTrace``s, hands them to the pure
``Feedback`` optimizer, and persists the returned prompts as a new
``OptimizationTarget``. The experiment's ``current_optimization_target_id``
pointer flips in the same transaction as the insert.
"""

from __future__ import annotations

from patientzero.feedback.feedback import Feedback
from patientzero.repositories import RepoSet
from patientzero.types import (
    FeedbackTrace,
    Message,
    OptimizationResult,
    OptimizationTarget,
)


class FeedbackService:
    def __init__(self, repos: RepoSet, feedback: Feedback | None = None):
        self.repos = repos
        self.feedback = feedback or Feedback()

    async def optimize(self, experiment_id: str) -> OptimizationResult:
        experiment = await self.repos.experiments.get(experiment_id)
        if experiment is None:
            raise ValueError(f"Experiment {experiment_id!r} not found")

        current_target = await self._require_current_target(experiment_id, experiment.current_optimization_target_id)
        traces = await self._build_traces(experiment_id)
        model = experiment.config.model

        new_prompts, rationale = await self.feedback.run(current_target, traces, model)

        async with self.repos.optimization_targets.transaction():
            persisted = await self.repos.optimization_targets.create(
                experiment_id=experiment_id,
                kind=current_target.kind,
                prompts=new_prompts,
                parent_id=current_target.id,
            )
            await self.repos.experiments.set_current_optimization_target(experiment_id, persisted.id)

        return OptimizationResult(
            new_target=persisted,
            previous_target=current_target,
            rationale=rationale,
            traces_considered=len(traces),
        )

    # ── Helpers ─────────────────────────────────────────────────────────────

    async def _require_current_target(
        self,
        experiment_id: str,
        current_id: str | None,
    ) -> OptimizationTarget:
        if current_id is None:
            raise ValueError(f"Experiment {experiment_id!r} has no current optimization target")
        target = await self.repos.optimization_targets.get(current_id)
        if target is None:
            raise ValueError(f"Experiment {experiment_id!r} points at unknown target {current_id!r}")
        return target

    async def _build_traces(self, experiment_id: str) -> list[FeedbackTrace]:
        pairs = await self.repos.evaluations.list_completed_with_evaluations_for_experiment(experiment_id)
        traces: list[FeedbackTrace] = []
        for sim, ev in pairs:
            turns = await self.repos.simulations.get_turns(sim.id)
            transcript = [Message(role=t.role, content=t.content) for t in turns]
            primary = ev.judge_results[0] if ev.judge_results else None
            traces.append(FeedbackTrace(
                simulation_id=sim.id,
                profiles={k: dict(v) for k, v in sim.config.profiles.items()},
                transcript=transcript,
                scores=dict(primary.scores) if primary else {},
                justification=primary.justification if (primary and primary.justification) else "",
            ))
        return traces
