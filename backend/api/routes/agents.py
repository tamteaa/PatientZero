import re

from fastapi import APIRouter, HTTPException

from backend.api.dependencies import repos

router = APIRouter()

_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def _variables_from_template(template: str) -> list[dict]:
    names = list(dict.fromkeys(_PLACEHOLDER_RE.findall(template)))
    return [
        {"name": n, "source": "profile/trait", "description": f"Value for {n!r}."}
        for n in names
    ]


def _agent_entry(name: str, template: str, model: str | None) -> dict:
    return {
        "name": name,
        "template": template,
        "variables": _variables_from_template(template),
        "extras": {},
        "model_note": f"Model: {model}" if model else "Uses experiment default model.",
    }


@router.get("/agents/config")
async def get_agents_config():
    """Global agents config derived from the first experiment's current
    optimization target, for the frontend's Doctor/Patient/Judge pages."""
    experiments = await repos.experiments.list_all()
    if not experiments:
        raise HTTPException(status_code=404, detail="No experiments available")
    exp = experiments[0]
    target_id = exp.current_optimization_target_id
    target_prompts: dict[str, str] = {}
    if target_id is not None:
        target = await repos.optimization_targets.get(target_id)
        if target is not None:
            target_prompts = target.prompts

    agents_by_name = {a.name: a for a in exp.config.agents}
    out: dict[str, dict] = {}
    for key in ("doctor", "patient"):
        agent = agents_by_name.get(key)
        if agent is None:
            continue
        template = target_prompts.get(key, agent.prompt)
        out[key] = _agent_entry(key, template, agent.model)
    judge = exp.config.judge
    judge_template = (
        (judge.instructions or "") +
        ("\n\nRubric:\n" + "\n".join(f"- {k}: {v}" for k, v in judge.rubric.items())
         if judge.rubric else "")
    )
    out["judge"] = _agent_entry("judge", judge_template, judge.model)
    return out


@router.get("/experiments/{exp_id}/agents")
async def get_experiment_agents(exp_id: str):
    experiment = await repos.experiments.get(exp_id)
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
