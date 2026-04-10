from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from backend.api.dependencies import db
from core.analysis.coverage import compute_coverage
from core.db.queries.experiments import (
    create_experiment,
    delete_experiment,
    get_experiment,
    list_experiments,
)
from core.db.queries.simulations import list_simulations

router = APIRouter()


class CreateExperimentRequest(BaseModel):
    name: str


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


@router.get("/experiments/{exp_id}/coverage")
def get_experiment_coverage(exp_id: str):
    exp = get_experiment(db, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    sims = [s for s in list_simulations(db) if s.experiment_id == exp_id]
    return compute_coverage(sims, exp.patient_distribution, exp.doctor_distribution).to_dict()
