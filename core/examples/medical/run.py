import asyncio

from core import Experiment
from core.config.settings import DB_PATH
from core.db.database import Database
from core.examples.medical.config import MEDICAL_EXAMPLE_CONFIG
from core.repositories import RepoSet


SIMS_PER_ROUND = 2


def _fmt_scores(scores: dict[str, float]) -> str:
    if not scores:
        return "(no scores yet)"
    return ", ".join(f"{k}={v:.2f}" for k, v in scores.items())


async def main():
    db = Database(DB_PATH)
    db.init()
    repos = RepoSet.for_db(db)
    exp = Experiment(MEDICAL_EXAMPLE_CONFIG, repos)
    total_rounds = 1 + exp.config.num_optimizations

    print(f"experiment: {exp.id}")
    print(f"rounds: {total_rounds}  sims/round: {SIMS_PER_ROUND}  num_optimizations: {exp.config.num_optimizations}")

    for round_idx in range(total_rounds):
        if round_idx > 0:
            print(f"\n── round {round_idx}: optimizing ──")
            result = await exp.optimize()
            print(f"  previous target: {result.previous_target.id[:8]}")
            print(f"  new target:      {result.new_target.id[:8]}")
            print(f"  traces considered: {result.traces_considered}")
            print(f"  rationale: {result.rationale[:200]}...")

        target_id = exp.record.current_optimization_target_id
        print(f"\n── round {round_idx}: running {SIMS_PER_ROUND} sims on target {target_id[:8]} ──")
        sim_ids = await exp.run(n=SIMS_PER_ROUND)
        for sim_id in sim_ids:
            sim = repos.simulations.get(sim_id)
            print(f"  {sim_id[:8]} state={sim.state} duration_ms={sim.duration_ms:.0f}")
        print(f"  scores (this target): {_fmt_scores(exp.scores(target_id))}")

    print("\n── final ──")
    for target in exp.history():
        target_scores = exp.scores(target.id)
        marker = " (current)" if target.id == exp.record.current_optimization_target_id else ""
        print(f"  {target.id[:8]}{marker}: {_fmt_scores(target_scores)}")


if __name__ == "__main__":
    asyncio.run(main())
