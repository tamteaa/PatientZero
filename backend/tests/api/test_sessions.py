def test_create_session(test_client):
    resp = test_client.post("/api/sessions", json={"model": "mock:default"})
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert data["title"] == "New Chat"
    assert data["model"] == "mock:default"


def test_list_sessions(test_client):
    test_client.post("/api/sessions", json={})
    test_client.post("/api/sessions", json={})
    resp = test_client.get("/api/sessions")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_session_detail(test_client):
    create_resp = test_client.post("/api/sessions", json={})
    session_id = create_resp.json()["id"]
    resp = test_client.get(f"/api/sessions/{session_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == session_id
    assert "turns" in data


def test_get_session_not_found(test_client):
    resp = test_client.get("/api/sessions/nonexistent")
    assert resp.status_code == 404


def test_patch_session_model(test_client):
    create_resp = test_client.post("/api/sessions", json={})
    session_id = create_resp.json()["id"]
    resp = test_client.patch(f"/api/sessions/{session_id}", json={"model": "openai:gpt-4o"})
    assert resp.status_code == 200
    assert resp.json()["model"] == "openai:gpt-4o"


def test_patch_session_not_found(test_client):
    resp = test_client.patch("/api/sessions/nonexistent", json={"model": "mock:default"})
    assert resp.status_code == 404


def test_get_models(test_client):
    resp = test_client.get("/api/models")
    assert resp.status_code == 200
    models = resp.json()
    assert isinstance(models, list)
    assert "mock:default" in models
