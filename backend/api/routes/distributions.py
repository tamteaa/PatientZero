from fastapi import APIRouter, HTTPException

from backend.api.dependencies import repos
from patientzero.distribution import distribution_to_dict

router = APIRouter()


@router.get("/experiments/{exp_id}/distributions/{agent_name}")
def get_agent_distribution(exp_id: str, agent_name: str):
    experiment = repos.experiments.get(exp_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    try:
        agent = experiment.config.agent(agent_name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name!r} not found in experiment")
    return {"distribution": distribution_to_dict(agent.distribution)}
