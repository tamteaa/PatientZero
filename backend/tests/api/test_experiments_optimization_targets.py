from patientzero import Agent, Distribution, Experiment
from patientzero.types import ExperimentConfig, JudgeConfig


def _other_config(name: str) -> ExperimentConfig:
    return ExperimentConfig(
        name=name,
        agents=(
            Agent("doctor", "Doctor {empathy}", Distribution(empathy={"low": 1.0})),
            Agent("patient", "Patient {literacy}", Distribution(literacy={"low": 1.0})),
        ),
        judge=JudgeConfig(rubric={"score": "Overall."}, instructions="Evaluate.", model=None),
        model="mock:default",
    )


def test_list_optimization_targets(test_client, experiment):
    resp = test_client.get(f"/api/experiments/{experiment.id}/optimization-targets")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["id"]
    assert data[0]["experiment_id"] == experiment.id


def test_set_current_optimization_target(test_client, experiment):
    current_id = experiment.current_optimization_target_id
    assert current_id
    resp = test_client.post(
        f"/api/experiments/{experiment.id}/optimization-target/current",
        json={"optimization_target_id": current_id},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["current_optimization_target_id"] == current_id


def test_set_current_optimization_target_wrong_experiment(test_client, experiment, db):
    other = Experiment(_other_config("other"), db).record
    other_target_id = other.current_optimization_target_id
    resp = test_client.post(
        f"/api/experiments/{experiment.id}/optimization-target/current",
        json={"optimization_target_id": other_target_id},
    )
    assert resp.status_code == 404
