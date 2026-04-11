from core.db.queries.experiments import create_experiment
from core.db.queries.optimization_targets import list_optimization_targets


def test_list_optimization_targets(test_client, experiment):
    resp = test_client.get(f"/api/experiments/{experiment.id}/optimization-targets")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["id"]
    assert data[0]["experiment_id"] == experiment.id


def test_set_current_optimization_target(test_client, experiment, db):
    _ = list_optimization_targets(db, experiment.id)
    # Re-point to the same initial target (no-op) still returns 200
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
    other = create_experiment(db, name="other")
    other_targets = list_optimization_targets(db, other.id)
    foreign_id = other_targets[0].id
    resp = test_client.post(
        f"/api/experiments/{experiment.id}/optimization-target/current",
        json={"optimization_target_id": foreign_id},
    )
    assert resp.status_code == 404


def test_compare_analysis_accepts_batch_id_alias(test_client):
    r = test_client.get(
        "/api/analysis/compare",
        params={"baseline_batch_id": "a", "candidate_batch_id": "b"},
    )
    assert r.status_code == 200
    j = r.json()
    assert j["baseline_batch_id"] == "a"
    assert j["candidate_batch_id"] == "b"


def test_compare_analysis_legacy_params(test_client):
    r = test_client.get(
        "/api/analysis/compare",
        params={"baseline_experiment_id": "x", "candidate_experiment_id": "y"},
    )
    assert r.status_code == 200
    j = r.json()
    assert j["baseline_experiment_id"] == "x"


def test_compare_analysis_requires_ids(test_client):
    r = test_client.get("/api/analysis/compare")
    assert r.status_code == 400
