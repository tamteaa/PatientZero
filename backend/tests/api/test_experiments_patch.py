from core.db.queries.experiments import get_experiment


def test_patch_experiment_sampling_seed(test_client, experiment):
    r = test_client.patch(
        f"/api/experiments/{experiment.id}",
        json={"sampling_seed": 999},
    )
    assert r.status_code == 200
    assert r.json()["sampling_seed"] == 999


def test_patch_experiment_clear_seed(test_client, experiment):
    test_client.patch(f"/api/experiments/{experiment.id}", json={"sampling_seed": 42})
    r = test_client.patch(f"/api/experiments/{experiment.id}", json={"sampling_seed": None})
    assert r.status_code == 200
    assert r.json()["sampling_seed"] is None


def test_patch_experiment_reset_draw_index(test_client, experiment, db):
    test_client.patch(f"/api/experiments/{experiment.id}", json={"sampling_seed": 1})
    test_client.post(
        "/api/simulate",
        json={"experiment_id": experiment.id, "model": "mock:default"},
    )
    assert get_experiment(db, experiment.id).sample_draw_index >= 1
    test_client.patch(
        f"/api/experiments/{experiment.id}",
        json={"reset_sample_draw_index": True},
    )
    assert get_experiment(db, experiment.id).sample_draw_index == 0
