import time


def test_patch_reset_sample_draw_index(test_client, experiment, repos):
    # Seed is set via ExperimentConfig at creation; the test fixture has no seed,
    # so draw_index will stay at 0. Running a simulation still bumps nothing, but
    # PATCH reset must be a no-op that succeeds.
    r = test_client.patch(f"/api/experiments/{experiment.id}")
    assert r.status_code == 200
    assert repos.experiments.get(experiment.id).sample_draw_index == 0
