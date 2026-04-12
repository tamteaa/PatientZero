"""
Coverage analysis for an experiment.

A **cell** is a tuple of (trait_name, trait_value) pairs across every agent
in the experiment. Target cell probabilities are estimated via Monte Carlo
draws through the agents' distributions, which matches the joint the
simulator actually samples.

Coverage % = sum of target mass on cells hit at least once by completed
simulations.

``distribution_match`` = ``1 - TVD`` between the Monte Carlo target and the
empirical cell distribution of counted simulations (``None`` if nothing to
compare).
"""

from __future__ import annotations

import math
import random
from collections import Counter

from patientzero.agent import Agent
from patientzero.types import CoverageReport, SimulationRecord

DEFAULT_MC_SAMPLES = 100_000
COVERAGE_PROBABILITY_FLOOR = 0.01

Cell = tuple[tuple[str, str], ...]  # sorted ((agent.trait, value), ...)


def _profiles_to_cell(profiles: dict[str, dict[str, str]]) -> Cell:
    pairs: list[tuple[str, str]] = []
    for agent_name in sorted(profiles.keys()):
        for trait in sorted(profiles[agent_name].keys()):
            pairs.append((f"{agent_name}.{trait}", profiles[agent_name][trait]))
    return tuple(pairs)


def _sim_to_cell(sim: SimulationRecord) -> Cell | None:
    try:
        return _profiles_to_cell(sim.config.profiles)
    except (KeyError, AttributeError):
        return None


def _build_target_cells(
    agents: tuple[Agent, ...],
    n_samples: int,
    rng: random.Random | None = None,
) -> dict[Cell, float]:
    r = rng or random.Random()
    counts: Counter[Cell] = Counter()
    for _ in range(n_samples):
        profiles = {agent.name: agent.sample(rng=r) for agent in agents}
        counts[_profiles_to_cell(profiles)] += 1
    total = sum(counts.values())
    if total == 0:
        return {}
    return {c: counts[c] / total for c in counts}


def _tvd(p: dict[Cell, float], q: dict[Cell, float]) -> float:
    keys = set(p) | set(q)
    return 0.5 * sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in keys)


def _empirical_from_sims(sims: list[SimulationRecord], cell_keys: set[Cell]) -> dict[Cell, float]:
    observed: list[Cell] = []
    for sim in sims:
        c = _sim_to_cell(sim)
        if c and c in cell_keys:
            observed.append(c)
    if not observed:
        return {}
    cnt = Counter(observed)
    n = len(observed)
    return {cell: cnt[cell] / n for cell in cnt}


def compute_coverage(
    sims: list[SimulationRecord],
    agents: tuple[Agent, ...],
    *,
    samples: int = DEFAULT_MC_SAMPLES,
    rng: random.Random | None = None,
) -> CoverageReport:
    cell_targets = _build_target_cells(agents, samples, rng=rng)

    hit_cells: set[Cell] = set()
    counted = 0
    for sim in sims:
        cell = _sim_to_cell(sim)
        if cell is None or cell not in cell_targets:
            continue
        hit_cells.add(cell)
        counted += 1

    coverage_pct = sum(cell_targets[c] for c in hit_cells)

    reasonable = [p for p in cell_targets.values() if p >= COVERAGE_PROBABILITY_FLOOR]
    if reasonable:
        estimated_needed = math.ceil(1.0 / min(reasonable))
    else:
        nonzero = [p for p in cell_targets.values() if p > 0]
        estimated_needed = math.ceil(1.0 / min(nonzero)) if nonzero else 0

    dist_match: float | None = None
    if cell_targets and counted > 0:
        q = _empirical_from_sims(sims, set(cell_targets.keys()))
        if q:
            dist_match = round(1.0 - _tvd(cell_targets, q), 4)

    return CoverageReport(
        cells_total=len(cell_targets),
        cells_hit=len(hit_cells),
        simulations_counted=counted,
        coverage_pct=coverage_pct,
        estimated_total_needed=estimated_needed,
        target_method="monte_carlo",
        mc_samples=samples,
        distribution_match=dist_match,
    )
