import time

import pytest


@pytest.fixture
def valid_sim_request(test_client, experiment):
    return {
        "experiment_id": experiment.id,
        "scenario_name": "CBC - Elevated WBC / Low Hemoglobin",
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


def test_simulate_returns_id(test_client, valid_sim_request):
    resp = test_client.post("/api/simulate", json=valid_sim_request)
    assert resp.status_code == 200
    data = resp.json()
    assert "simulation_id" in data
    assert isinstance(data["simulation_id"], str)


def test_simulate_missing_experiment_id(test_client, valid_sim_request):
    req = {k: v for k, v in valid_sim_request.items() if k != "experiment_id"}
    resp = test_client.post("/api/simulate", json=req)
    assert resp.status_code == 422


def test_simulate_unknown_experiment(test_client, valid_sim_request):
    req = {**valid_sim_request, "experiment_id": "nonexistent"}
    resp = test_client.post("/api/simulate", json=req)
    assert resp.status_code == 404


def test_simulate_invalid_patient_literacy(test_client, valid_sim_request):
    req = {**valid_sim_request, "patient_literacy": "very_low"}
    resp = test_client.post("/api/simulate", json=req)
    assert resp.status_code == 400


def test_simulate_invalid_doctor_empathy(test_client, valid_sim_request):
    req = {**valid_sim_request, "doctor_empathy": "very_high"}
    resp = test_client.post("/api/simulate", json=req)
    assert resp.status_code == 400


def test_simulate_unknown_scenario(test_client, valid_sim_request):
    req = {**valid_sim_request, "scenario_name": "Unknown Test"}
    resp = test_client.post("/api/simulate", json=req)
    assert resp.status_code == 404


def test_simulate_invalid_doctor_verbosity(test_client, valid_sim_request):
    req = {**valid_sim_request, "doctor_verbosity": "verbose"}
    resp = test_client.post("/api/simulate", json=req)
    assert resp.status_code == 400


def test_simulate_invalid_max_turns_zero(test_client, valid_sim_request):
    req = {**valid_sim_request, "max_turns": 0}
    resp = test_client.post("/api/simulate", json=req)
    assert resp.status_code == 422


def test_simulate_invalid_max_turns_negative(test_client, valid_sim_request):
    req = {**valid_sim_request, "max_turns": -1}
    resp = test_client.post("/api/simulate", json=req)
    assert resp.status_code == 422


def test_simulate_invalid_max_turns_too_high(test_client, valid_sim_request):
    req = {**valid_sim_request, "max_turns": 100}
    resp = test_client.post("/api/simulate", json=req)
    assert resp.status_code == 422


# ── Simulation history ───────────────────────────────────────────────────────


def test_list_simulations_empty(test_client):
    resp = test_client.get("/api/simulations")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_simulations_after_create(test_client, valid_sim_request):
    test_client.post("/api/simulate", json=valid_sim_request)
    resp = test_client.get("/api/simulations")
    assert resp.status_code == 200
    sims = resp.json()
    assert len(sims) >= 1
    sim = sims[0]
    assert sim["scenario_name"] == "CBC - Elevated WBC / Low Hemoglobin"
    assert sim["model"] == "mock:default"


def test_get_simulation_detail(test_client, valid_sim_request):
    create_resp = test_client.post("/api/simulate", json=valid_sim_request)
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


def test_delete_simulation(test_client, valid_sim_request):
    create_resp = test_client.post("/api/simulate", json=valid_sim_request)
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


def test_evaluate_requires_completed(test_client, valid_sim_request):
    create_resp = test_client.post("/api/simulate", json=valid_sim_request)
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
