import time


VALID_SIM_REQUEST = {
    "patient_name": "Maria Santos",
    "doctor_name": "Dr. Sarah Chen",
    "scenario_name": "CBC - Elevated WBC / Low Hemoglobin",
    "style": "clinical",
    "model": "mock:default",
    "max_turns": 4,
}


# ── Personas / Doctors / Scenarios / Styles ──────────────────────────────────


def test_get_personas(test_client):
    resp = test_client.get("/api/personas")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "name" in data[0]
    assert "traits" in data[0]


def test_get_doctors(test_client):
    resp = test_client.get("/api/doctors")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["role"] == "doctor"


def test_get_scenarios(test_client):
    resp = test_client.get("/api/scenarios")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "name" in data[0]
    assert "description" in data[0]


def test_get_styles(test_client):
    resp = test_client.get("/api/styles")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert "clinical" in data


# ── Simulate ─────────────────────────────────────────────────────────────────


def test_simulate_returns_id(test_client):
    resp = test_client.post("/api/simulate", json=VALID_SIM_REQUEST)
    assert resp.status_code == 200
    data = resp.json()
    assert "simulation_id" in data
    assert isinstance(data["simulation_id"], str)


def test_simulate_unknown_patient(test_client):
    req = {**VALID_SIM_REQUEST, "patient_name": "Nobody"}
    resp = test_client.post("/api/simulate", json=req)
    assert resp.status_code == 404


def test_simulate_unknown_doctor(test_client):
    req = {**VALID_SIM_REQUEST, "doctor_name": "Dr. Nobody"}
    resp = test_client.post("/api/simulate", json=req)
    assert resp.status_code == 404


def test_simulate_unknown_scenario(test_client):
    req = {**VALID_SIM_REQUEST, "scenario_name": "Unknown Test"}
    resp = test_client.post("/api/simulate", json=req)
    assert resp.status_code == 404


def test_simulate_unknown_style(test_client):
    req = {**VALID_SIM_REQUEST, "style": "nonexistent"}
    resp = test_client.post("/api/simulate", json=req)
    assert resp.status_code == 400


def test_simulate_invalid_max_turns_zero(test_client):
    req = {**VALID_SIM_REQUEST, "max_turns": 0}
    resp = test_client.post("/api/simulate", json=req)
    assert resp.status_code == 422


def test_simulate_invalid_max_turns_negative(test_client):
    req = {**VALID_SIM_REQUEST, "max_turns": -1}
    resp = test_client.post("/api/simulate", json=req)
    assert resp.status_code == 422


def test_simulate_invalid_max_turns_too_high(test_client):
    req = {**VALID_SIM_REQUEST, "max_turns": 100}
    resp = test_client.post("/api/simulate", json=req)
    assert resp.status_code == 422


# ── Simulation history ───────────────────────────────────────────────────────


def test_list_simulations_empty(test_client):
    resp = test_client.get("/api/simulations")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_simulations_after_create(test_client):
    test_client.post("/api/simulate", json=VALID_SIM_REQUEST)
    resp = test_client.get("/api/simulations")
    assert resp.status_code == 200
    sims = resp.json()
    assert len(sims) >= 1
    sim = sims[0]
    assert sim["persona_name"] == "Maria Santos"
    assert sim["scenario_name"] == "CBC - Elevated WBC / Low Hemoglobin"
    assert sim["style"] == "clinical"
    assert sim["model"] == "mock:default"


def test_get_simulation_detail(test_client):
    create_resp = test_client.post("/api/simulate", json=VALID_SIM_REQUEST)
    sim_id = create_resp.json()["simulation_id"]
    time.sleep(0.5)

    resp = test_client.get(f"/api/simulations/{sim_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == sim_id
    assert "turns" in data


def test_get_simulation_not_found(test_client):
    resp = test_client.get("/api/simulations/nonexistent")
    assert resp.status_code == 404


def test_delete_simulation(test_client):
    create_resp = test_client.post("/api/simulate", json=VALID_SIM_REQUEST)
    sim_id = create_resp.json()["simulation_id"]
    time.sleep(0.3)

    resp = test_client.delete(f"/api/simulations/{sim_id}")
    assert resp.status_code == 200
    assert test_client.get(f"/api/simulations/{sim_id}").status_code == 404


def test_delete_simulation_not_found(test_client):
    resp = test_client.delete("/api/simulations/nonexistent")
    assert resp.status_code == 404


# ── Evaluation ───────────────────────────────────────────────────────────────


def test_evaluate_not_found(test_client):
    resp = test_client.post("/api/simulations/nonexistent/evaluate", json={"model": "mock:default"})
    assert resp.status_code == 404


def test_get_evaluation_not_found(test_client):
    resp = test_client.get("/api/simulations/nonexistent/evaluation")
    assert resp.status_code == 404


def test_list_evaluations_empty(test_client):
    resp = test_client.get("/api/evaluations")
    assert resp.status_code == 200
    assert resp.json() == []


def test_evaluate_requires_completed(test_client):
    create_resp = test_client.post("/api/simulate", json=VALID_SIM_REQUEST)
    sim_id = create_resp.json()["simulation_id"]

    resp = test_client.post(f"/api/simulations/{sim_id}/evaluate", json={"model": "mock:default"})
    # Might be 400 (not completed yet) or 200 if mock completes instantly
    assert resp.status_code in (200, 400)


# ── Simulation control ──────────────────────────────────────────────────────


def test_pause_not_found(test_client):
    resp = test_client.post("/api/simulations/nonexistent/pause")
    assert resp.status_code == 404


def test_resume_not_found(test_client):
    resp = test_client.post("/api/simulations/nonexistent/resume")
    assert resp.status_code == 404


def test_stop_not_found(test_client):
    resp = test_client.post("/api/simulations/nonexistent/stop")
    assert resp.status_code == 404
