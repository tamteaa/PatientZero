import backend.api.routes.experiments as experiments_routes


def test_optimize_returns_result(test_client, experiment):
    resp = test_client.post(f"/api/experiments/{experiment.id}/optimize", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert "new_target" in data
    assert data["new_target"]["id"]


def test_optimize_conflict_when_semaphore_busy(test_client, experiment, monkeypatch):
    def busy_acquire(blocking=True):
        return False

    monkeypatch.setattr(experiments_routes._optimize_semaphore, "acquire", busy_acquire)

    resp = test_client.post(f"/api/experiments/{experiment.id}/optimize", json={})
    assert resp.status_code == 409
    assert "detail" in resp.json()
