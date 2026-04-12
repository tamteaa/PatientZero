from fastapi import APIRouter, HTTPException

from backend.api.dependencies import repos

router = APIRouter()


@router.get("/experiments/{exp_id}/agents")
def get_experiment_agents(exp_id: str):
    experiment = repos.experiments.get(exp_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    config = experiment.config
    return {
        "agents": [
            {"name": a.name, "prompt": a.prompt, "model": a.model}
            for a in config.agents
        ],
        "judge": {
            "rubric": dict(config.judge.rubric),
            "instructions": config.judge.instructions,
            "model": config.judge.model,
        },
    }
