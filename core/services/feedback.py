"""
FeedbackService — orchestrates one feedback loop run.

Loads the experiment's current target, its recent evaluated simulations,
builds a FeedbackSignal, invokes the pure Feedback class to produce an
OptimizationResult, persists the winning new target, and updates the
experiment's `current_optimization_target_id` pointer.
"""

import json

from core.db.database import Database
from core.db.queries.evaluations import list_evaluations
from core.db.queries.experiments import (
    get_experiment,
    set_current_optimization_target,
)
from core.db.queries.optimization_targets import (
    create_optimization_target,
    get_optimization_target,
)
from core.db.queries.simulations import get_simulation_turns, list_simulations
from core.feedback.feedback import Feedback
from core.feedback.template_validation import PromptTemplateError, validate_optimization_prompts
from core.types import (
    EvaluationRecord,
    FailureCase,
    FeedbackSignal,
    Message,
    OptimizationConfig,
    OptimizationMetric,
    OptimizationRequest,
    OptimizationResult,
    OptimizationTarget,
    SimulationRecord,
)

_JUDGE_DIMENSIONS = [
    "comprehension_score",
    "factual_recall",
    "applied_reasoning",
    "explanation_quality",
    "interaction_quality",
]


class FeedbackService:
    def __init__(self, db: Database, feedback: Feedback | None = None):
        self.db = db
        self.feedback = feedback or Feedback()

    def optimize(self, experiment_id: str, config: OptimizationConfig) -> OptimizationResult:
        experiment = get_experiment(self.db, experiment_id)
        if experiment is None:
            raise ValueError(f"Experiment {experiment_id!r} not found")
        if experiment.current_optimization_target_id is None:
            raise ValueError(f"Experiment {experiment_id!r} has no current optimization target")

        current_target = get_optimization_target(self.db, experiment.current_optimization_target_id)
        if current_target is None:
            raise ValueError("Current optimization target row is missing")

        signal = self._build_signal(experiment_id, config)

        request = OptimizationRequest(
            current_target=current_target,
            signal=signal,
            config=config,
        )

        result = self.feedback.run(request)

        try:
            validate_optimization_prompts(result.new_target.prompts)
        except PromptTemplateError as e:
            raise ValueError(str(e)) from e

        # Persist the winning candidate as a new row, then point the experiment at it.
        persisted = create_optimization_target(
            self.db,
            experiment_id=experiment_id,
            kind=result.new_target.kind,
            prompts=result.new_target.prompts,
            parent_id=current_target.id,
        )
        set_current_optimization_target(self.db, experiment_id, persisted.id)

        # Return a result whose new_target reflects the persisted row (real id + created_at).
        return OptimizationResult(
            new_target=persisted,
            baseline=result.baseline,
            candidates=result.candidates,
            improvement=result.improvement,
        )

    # ── Signal building ─────────────────────────────────────────────────────

    def _build_signal(self, experiment_id: str, config: OptimizationConfig) -> FeedbackSignal:
        sims: list[SimulationRecord] = [
            s for s in list_simulations(self.db)
            if s.experiment_id == experiment_id and s.state == "completed"
        ]
        if not sims:
            return FeedbackSignal(simulations_considered=0, mean_scores={}, worst_cases=[])

        evals_by_sim: dict[str, EvaluationRecord] = {
            e.simulation_id: e for e in list_evaluations(self.db)
        }
        pairs: list[tuple[SimulationRecord, EvaluationRecord]] = [
            (s, evals_by_sim[s.id]) for s in sims if s.id in evals_by_sim
        ]
        if not pairs:
            return FeedbackSignal(simulations_considered=0, mean_scores={}, worst_cases=[])

        mean_scores = self._mean_dimension_scores(pairs)
        worst_cases = self._worst_cases(pairs, config.metric, config.worst_cases_k)

        return FeedbackSignal(
            simulations_considered=len(pairs),
            mean_scores=mean_scores,
            worst_cases=worst_cases,
        )

    @staticmethod
    def _mean_dimension_scores(
        pairs: list[tuple[SimulationRecord, EvaluationRecord]],
    ) -> dict[str, float]:
        sums: dict[str, float] = {dim: 0.0 for dim in _JUDGE_DIMENSIONS}
        counts: dict[str, int] = {dim: 0 for dim in _JUDGE_DIMENSIONS}
        for _, ev in pairs:
            if not ev.judge_results:
                continue
            for dim in _JUDGE_DIMENSIONS:
                values = [
                    getattr(j, dim) for j in ev.judge_results if getattr(j, dim, None) is not None
                ]
                if values:
                    sums[dim] += sum(values) / len(values)
                    counts[dim] += 1
        return {dim: sums[dim] / counts[dim] for dim in _JUDGE_DIMENSIONS if counts[dim] > 0}

    def _worst_cases(
        self,
        pairs: list[tuple[SimulationRecord, EvaluationRecord]],
        metric: OptimizationMetric,
        k: int,
    ) -> list[FailureCase]:
        def sim_score(ev: EvaluationRecord) -> float:
            if not ev.judge_results:
                return float("inf")
            scores = [metric.score(j) for j in ev.judge_results]
            return sum(scores) / len(scores)

        ranked = sorted(pairs, key=lambda p: sim_score(p[1]))
        failures: list[FailureCase] = []
        for sim, ev in ranked[:k]:
            failures.append(self._failure_case(sim, ev))
        return failures

    def _failure_case(self, sim: SimulationRecord, ev: EvaluationRecord) -> FailureCase:
        config = json.loads(sim.config_json) if sim.config_json else {}
        patient_traits = config.get("patient", {}).get("traits", {})
        primary = ev.judge_results[0] if ev.judge_results else None
        scores = (
            {dim: int(getattr(primary, dim) or 0) for dim in _JUDGE_DIMENSIONS}
            if primary else {}
        )
        turns = get_simulation_turns(self.db, sim.id)
        transcript = [Message(role=t.role, content=t.content) for t in turns]
        return FailureCase(
            simulation_id=sim.id,
            scenario_name=sim.scenario_name,
            patient_traits=patient_traits,
            transcript=transcript,
            scores=scores,
            judge_justification=(primary.justification if primary and primary.justification else ""),
        )
