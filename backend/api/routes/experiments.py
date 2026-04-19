import threading

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from backend.api.dependencies import repos
from patientzero import Experiment
from patientzero.analysis.coverage import compute_coverage
from patientzero.config.settings import APP_SETTINGS
from patientzero.examples.medical import MEDICAL_EXAMPLE_CONFIG
from patientzero.services.feedback import FeedbackService

router = APIRouter()

_optimize_semaphore = threading.Semaphore(APP_SETTINGS.max_concurrent_optimizations)


class CreateExperimentRequest(BaseModel):
    name: str


class SetCurrentOptimizationTargetBody(BaseModel):
    optimization_target_id: str


async def _experiment_or_404(exp_id: str):
    exp = await repos.experiments.get(exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp


@router.post("/experiments")
async def post_experiment(request: CreateExperimentRequest):
    config = MEDICAL_EXAMPLE_CONFIG
    # Shallow-override the name for this instance.
    from dataclasses import replace
    named_config = replace(config, name=request.name)
    try:
        exp = await Experiment.create(named_config, repos.experiments.db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    record = exp.record
    counts = await repos.experiments.counts_for(record.id)
    return record.to_dict(counts=counts)


@router.get("/experiments")
async def get_experiments():
    exps = await repos.experiments.list_all()
    counts_by_id = await repos.experiments.counts_all()
    return [e.to_dict(counts=counts_by_id.get(e.id)) for e in exps]


@router.get("/experiments/{exp_id}")
async def get_experiment_by_id(exp_id: str):
    exp = await _experiment_or_404(exp_id)
    counts = await repos.experiments.counts_for(exp_id)
    return exp.to_dict(counts=counts)


@router.delete("/experiments/{exp_id}")
async def delete_experiment_by_id(exp_id: str):
    await _experiment_or_404(exp_id)
    await repos.experiments.delete(exp_id)
    return Response(status_code=204)


@router.patch("/experiments/{exp_id}")
async def patch_experiment(exp_id: str):
    """Currently only supports resetting the sample draw index."""
    await _experiment_or_404(exp_id)
    await repos.experiments.reset_sample_draw_index(exp_id)
    updated = await repos.experiments.get(exp_id)
    assert updated is not None
    counts = await repos.experiments.counts_for(exp_id)
    return updated.to_dict(counts=counts)


# ── Experiment-scoped lists ─────────────────────────────────────────────────


@router.get("/experiments/{exp_id}/simulations")
async def list_experiment_simulations(exp_id: str):
    await _experiment_or_404(exp_id)
    sims = await repos.simulations.list_for_experiment(exp_id)
    return [s.to_dict() for s in sims]


@router.get("/experiments/{exp_id}/evaluations")
async def list_experiment_evaluations(exp_id: str):
    await _experiment_or_404(exp_id)
    evals = await repos.evaluations.list_for_experiment(exp_id)
    return [e.to_dict() for e in evals]


# ── Optimization targets ────────────────────────────────────────────────────


@router.get("/experiments/{exp_id}/optimization-targets")
async def list_experiment_optimization_targets(exp_id: str):
    await _experiment_or_404(exp_id)
    targets = await repos.optimization_targets.list_for_experiment(exp_id)
    return [t.to_dict() for t in targets]


@router.post("/experiments/{exp_id}/optimization-target/current")
async def set_experiment_current_optimization_target(
    exp_id: str, body: SetCurrentOptimizationTargetBody
):
    await _experiment_or_404(exp_id)
    target = await repos.optimization_targets.get(body.optimization_target_id)
    if target is None or target.experiment_id != exp_id:
        raise HTTPException(status_code=404, detail="Optimization target not found for this experiment")
    await repos.experiments.set_current_optimization_target(exp_id, body.optimization_target_id)
    updated = await repos.experiments.get(exp_id)
    assert updated is not None
    counts = await repos.experiments.counts_for(exp_id)
    return updated.to_dict(counts=counts)


# ── Coverage ────────────────────────────────────────────────────────────────


@router.get("/experiments/{exp_id}/coverage")
async def get_experiment_coverage(
    exp_id: str,
    mc_samples: int = Query(100_000, ge=5_000, le=500_000),
):
    exp = await _experiment_or_404(exp_id)
    sims = await repos.simulations.list_for_experiment(exp_id)
    return compute_coverage(sims, exp.config.agents, samples=mc_samples).to_dict()


# ── Optimize ────────────────────────────────────────────────────────────────


@router.post("/experiments/{exp_id}/optimize")
async def optimize_experiment(exp_id: str):
    await _experiment_or_404(exp_id)

    if not _optimize_semaphore.acquire(blocking=False):
        raise HTTPException(
            status_code=409,
            detail=(
                "Another optimization run is in progress "
                f"(max_concurrent_optimizations={APP_SETTINGS.max_concurrent_optimizations})"
            ),
        )
    try:
        try:
            result = await FeedbackService(repos).optimize(exp_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return result.to_dict()
    finally:
        _optimize_semaphore.release()
