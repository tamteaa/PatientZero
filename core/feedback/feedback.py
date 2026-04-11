"""
Feedback — the core domain class that turns an OptimizationRequest into an
OptimizationResult.

The real implementation will plug DSPy in here. This is the pure part of
the feedback loop: no DB, no persistence, no FastAPI — just signal in,
result out.

Current body is a stub: it mints a new target by lightly marking the
parent's prompts, and fabricates monotonic candidate scores around a
baseline derived from the signal. For DSPy wiring, start from
``core.llm.dspy_adapter`` and replace ``Feedback.run`` when ready.
"""

import uuid
from datetime import datetime

from core.types import (
    CandidateScore,
    OptimizationRequest,
    OptimizationResult,
    OptimizationTarget,
)


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


class Feedback:
    """
    Stateless optimizer. Takes an OptimizationRequest, returns an
    OptimizationResult. No side effects — the service layer persists
    the result separately.
    """

    def run(self, request: OptimizationRequest) -> OptimizationResult:
        config = request.config
        current = request.current_target

        baseline_score = self._baseline_score(request)
        baseline = CandidateScore(
            target=current,
            mean_score=baseline_score,
            trial_count=request.signal.simulations_considered,
        )

        candidates: list[CandidateScore] = []
        for i in range(config.num_candidates):
            candidate_target = self._stub_candidate(current, suffix=str(i + 1))
            candidate_score = baseline_score + (i + 1) * 0.5
            candidates.append(
                CandidateScore(
                    target=candidate_target,
                    mean_score=candidate_score,
                    trial_count=config.trials_per_candidate,
                )
            )

        winner = max(candidates, key=lambda c: c.mean_score)
        return OptimizationResult(
            new_target=winner.target,
            baseline=baseline,
            candidates=candidates,
            improvement=winner.mean_score - baseline_score,
        )

    # ── Stub helpers — replace when DSPy is integrated ──────────────────────

    @staticmethod
    def _baseline_score(request: OptimizationRequest) -> float:
        mean_scores = request.signal.mean_scores
        if not mean_scores:
            return 0.0
        return sum(
            weight * mean_scores.get(name, 0.0)
            for name, weight in request.config.metric.weights.items()
        )

    @staticmethod
    def _stub_candidate(parent: OptimizationTarget, suffix: str) -> OptimizationTarget:
        marked_prompts = {
            name: f"{template}\n\n<!-- stub candidate {suffix}: optimizer not yet implemented -->"
            for name, template in parent.prompts.items()
        }
        return OptimizationTarget(
            id=str(uuid.uuid4()),
            experiment_id=parent.experiment_id,
            kind=parent.kind,
            prompts=marked_prompts,
            parent_id=parent.id,
            created_at=_now(),
        )
