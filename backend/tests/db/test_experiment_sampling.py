from core.db.queries.experiments import (
    acquire_next_sample_rng,
    create_experiment,
    get_experiment,
    reset_experiment_sample_draw_index,
    set_experiment_sampling_seed,
)
from core.sampling import stable_rng


def test_acquire_next_sample_rng_none_without_seed(db):
    exp = create_experiment(db, name="e")
    assert acquire_next_sample_rng(db, exp.id) is None


def test_acquire_next_sample_rng_deterministic_and_increments(db):
    exp = create_experiment(db, name="e")
    set_experiment_sampling_seed(db, exp.id, 12345)
    r0 = acquire_next_sample_rng(db, exp.id)
    r1 = acquire_next_sample_rng(db, exp.id)
    assert r0 is not None and r1 is not None
    assert r0.randint(0, 10_000_000) == stable_rng(12345, 0).randint(0, 10_000_000)
    assert r1.randint(0, 10_000_000) == stable_rng(12345, 1).randint(0, 10_000_000)
    updated = get_experiment(db, exp.id)
    assert updated is not None
    assert updated.sample_draw_index == 2


def test_reset_sample_draw_index(db):
    exp = create_experiment(db, name="e")
    set_experiment_sampling_seed(db, exp.id, 1)
    acquire_next_sample_rng(db, exp.id)
    reset_experiment_sample_draw_index(db, exp.id)
    again = get_experiment(db, exp.id)
    assert again is not None
    assert again.sample_draw_index == 0
