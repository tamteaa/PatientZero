from typing import Literal

import threading

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from backend.api.dependencies import db
from core.analysis.coverage import compute_coverage
from core.config.settings import APP_SETTINGS
from core.db.queries.experiments import (
    create_experiment,
    delete_experiment,
    get_experiment,
    list_experiments,
    reset_experiment_sample_draw_index,
    set_current_optimization_target,
    set_experiment_sampling_seed,
)
from core.db.queries.optimization_targets import (
    get_optimization_target,
    list_optimization_targets,
)
from core.db.queries.simulations import list_simulations
from core.services.feedback import FeedbackService
from core.types import (
    OptimizationConfig,
    OptimizationMetric,
    SeedingMode,
)

router = APIRouter()

# Process-wide guard: at most N concurrent optimize runs (default 1).
_optimize_semaphore = threading.Semaphore(APP_SETTINGS.max_concurrent_optimizations)


class CreateExperimentRequest(BaseModel):
    name: str


class SetCurrentOptimizationTargetBody(BaseModel):
    optimization_target_id: str


class PatchExperimentRequest(BaseModel):
    """Only fields you send are applied. Send ``sampling_seed: null`` to clear the seed."""

    sampling_seed: int | None = Field(default=None)
    reset_sample_draw_index: bool = False


@router.post("/experiments")
def post_experiment(request: CreateExperimentRequest):
    exp = create_experiment(db, name=request.name)
    return exp.to_summary_dict()


@router.get("/experiments")
def get_experiments():
    return [e.to_summary_dict() for e in list_experiments(db)]


@router.get("/experiments/{exp_id}")
def get_experiment_by_id(exp_id: str):
    exp = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp.to_dict()


@router.delete("/experiments/{exp_id}")
def delete_experiment_by_id(exp_id: str):
    exp = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    delete_experiment(db, exp_id)
    return Response(status_code=204)


@router.patch("/experiments/{exp_id}")
def patch_experiment(exp_id: str, body: PatchExperimentRequest):
    exp = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    data = body.model_dump(exclude_unset=True)
    if "sampling_seed" in data:
        set_experiment_sampling_seed(db, exp_id, data["sampling_seed"])
    if data.get("reset_sample_draw_index"):
        reset_experiment_sample_draw_index(db, exp_id)
    updated = get_experiment(db, exp_id)
    assert updated is not None
    return updated.to_dict()


@router.get("/experiments/{exp_id}/optimization-targets")
def list_experiment_optimization_targets(exp_id: str):
    exp = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return [t.to_dict() for t in list_optimization_targets(db, exp_id)]


@router.post("/experiments/{exp_id}/optimization-target/current")
def set_experiment_current_optimization_target(
    exp_id: str, body: SetCurrentOptimizationTargetBody
):
    exp = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    target = get_optimization_target(db, body.optimization_target_id)
    if target is None or target.experiment_id != exp_id:
        raise HTTPException(status_code=404, detail="Optimization target not found for this experiment")
    set_current_optimization_target(db, exp_id, body.optimization_target_id)
    updated = get_experiment(db, exp_id)
    assert updated is not None
    return updated.to_dict()


@router.get("/experiments/{exp_id}/coverage")
def get_experiment_coverage(
    exp_id: str,
    target_method: Literal["monte_carlo", "independence"] = "monte_carlo",
    mc_samples: int = Query(100_000, ge=5_000, le=500_000),
):
    exp = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    sims = [s for s in list_simulations(db) if s.experiment_id == exp_id]
    return compute_coverage(
        sims,
        exp.patient_distribution,
        exp.doctor_distribution,
        target_method=target_method,
        mc_samples=mc_samples,
    ).to_dict()


class OptimizeRequest(BaseModel):
    metric_weights: dict[str, float] = Field(
        default_factory=lambda: {"comprehension_score": 1.0},
        description="Judge dimensions → weights to optimize against",
    )
    seeding_mode: str = "historical_failures"
    num_candidates: int = Field(default=5, ge=1, le=50)
    trials_per_candidate: int = Field(default=10, ge=1, le=100)
    worst_cases_k: int = Field(default=5, ge=0, le=50)


@router.post("/experiments/{exp_id}/optimize")
def optimize_experiment(exp_id: str, request: OptimizeRequest):
    exp = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    acquired = _optimize_semaphore.acquire(blocking=False)
    if not acquired:
        raise HTTPException(
            status_code=409,
            detail=(
                "Another optimization run is in progress "
                f"(max_concurrent_optimizations={APP_SETTINGS.max_concurrent_optimizations})"
            ),
        )

    try:
        try:
            seeding_mode = SeedingMode(request.seeding_mode)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown seeding_mode: {request.seeding_mode}")

        config = OptimizationConfig(
            metric=OptimizationMetric(weights=request.metric_weights),
            seeding_mode=seeding_mode,
            num_candidates=request.num_candidates,
            trials_per_candidate=request.trials_per_candidate,
            worst_cases_k=request.worst_cases_k,
        )

        service = FeedbackService(db)
        try:
            result = service.optimize(exp_id, config)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        return result.to_dict()
    finally:
        _optimize_semaphore.release()
