import asyncio


async def test_get_models(test_client):
    resp = await test_client.get("/api/models")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_simulate_creates_and_runs(test_client, experiment):
    resp = await test_client.post(
        "/api/simulate",
        json={
            "experiment_id": experiment.id,
            "model": "mock:default",
            "max_turns": 4,
        },
    )
    assert resp.status_code == 200, resp.text
    sim_id = resp.json()["simulation_id"]

    # Poll briefly until the simulation finishes.
    for _ in range(50):
        detail = (await test_client.get(f"/api/simulations/{sim_id}")).json()
        if detail["state"] in ("completed", "error"):
            break
        await asyncio.sleep(0.05)

    assert detail["state"] == "completed"
    assert detail["config"]["experiment_id"] == experiment.id
    assert "doctor" in detail["config"]["profiles"]
    assert "patient" in detail["config"]["profiles"]


async def test_simulate_with_constraint(test_client, experiment):
    resp = await test_client.post(
        "/api/simulate",
        json={
            "experiment_id": experiment.id,
            "model": "mock:default",
            "max_turns": 2,
            "constraints": {"patient": {"literacy": "low"}},
        },
    )
    assert resp.status_code == 200
    sim_id = resp.json()["simulation_id"]
    for _ in range(50):
        detail = (await test_client.get(f"/api/simulations/{sim_id}")).json()
        if detail["state"] in ("completed", "error"):
            break
        await asyncio.sleep(0.05)
    assert detail["config"]["profiles"]["patient"]["literacy"] == "low"


async def test_simulate_unknown_experiment(test_client):
    resp = await test_client.post(
        "/api/simulate",
        json={"experiment_id": "nonexistent", "model": "mock:default"},
    )
    assert resp.status_code == 404


async def test_delete_simulation(test_client, experiment):
    resp = await test_client.post(
        "/api/simulate",
        json={"experiment_id": experiment.id, "model": "mock:default", "max_turns": 2},
    )
    sim_id = resp.json()["simulation_id"]
    for _ in range(50):
        if (await test_client.get(f"/api/simulations/{sim_id}")).json()["state"] == "completed":
            break
        await asyncio.sleep(0.05)
    r = await test_client.delete(f"/api/simulations/{sim_id}")
    assert r.status_code == 200
    assert (await test_client.get(f"/api/simulations/{sim_id}")).status_code == 404
