"""
Batch simulation runner — runs all personas × scenarios × conditions and saves to DB.

Usage:
    uv run python -m evaluations.simulate.batch_run [options]

Options:
    --model MODEL           LLM to use for simulations (default: mock:default)
    --judge-model MODEL     LLM to use for judge evaluation (default: same as --model)
    --evaluate              Run judge evaluation after each simulation
    --skip-existing         Skip combinations already in the DB (any state)
    --dry-run               Print what would run without executing
    --conditions COND,...   Comma-separated subset, e.g. clinical-static,analogy-dialog
    --personas NAME,...     Comma-separated persona names to run (default: all)
    --scenarios NAME,...    Comma-separated scenario test_names to run (default: all)

Examples:
    # Dry run to see what would be executed
    uv run python -m evaluations.simulate.batch_run --dry-run

    # Run all with mock provider
    uv run python -m evaluations.simulate.batch_run --model mock:default --skip-existing

    # Run with Kimi and auto-evaluate
    uv run python -m evaluations.simulate.batch_run --model kimi:kimi-k2.5 --evaluate --skip-existing
"""

import argparse
import asyncio
import sys
from datetime import datetime

from core.agents.explainer import ExplainerAgent
from core.agents.judge import JudgeAgent
from core.agents.patient import PatientAgent
from core.config.personas import PERSONAS
from core.config.scenarios import SCENARIOS
from core.config.settings import DB_PATH
from core.db.database import Database
from core.db.queries.evaluations import create_evaluation, delete_evaluation, get_evaluation
from core.db.queries.simulations import (
    add_simulation_turn,
    complete_simulation,
    create_simulation,
    fail_simulation,
    get_simulation_turns,
    list_simulations,
)
from core.llm.factory import parse_provider_model
from core.simulation import Simulation

ALL_CONDITIONS = [
    ("clinical", "static"),
    ("clinical", "dialog"),
    ("analogy", "static"),
    ("analogy", "dialog"),
]


def condition_key(style: str, mode: str) -> str:
    return f"{style}-{mode}"


async def run_one(
    db: Database,
    persona,
    scenario,
    style: str,
    mode: str,
    model: str,
    judge_model: str,
    evaluate: bool,
) -> bool:
    """Run one simulation (and optionally evaluate it). Returns True on success."""
    provider, llm_model = parse_provider_model(model)

    explainer = ExplainerAgent(provider, llm_model, style, mode, scenario)
    patient = PatientAgent(provider, llm_model, persona)
    sim = Simulation(explainer, patient, mode)

    from dataclasses import asdict
    sim_record = create_simulation(
        db,
        persona_name=persona.name,
        scenario_name=scenario.test_name,
        style=style,
        mode=mode,
        model=model,
        config={
            "persona": asdict(persona),
            "scenario": asdict(scenario),
            "style": style,
            "mode": mode,
            "model": model,
        },
    )
    sim_id = sim_record["id"]

    try:
        async for event_type, data in sim.run_streaming():
            if event_type == "turn_end":
                step = sim.trace.steps[-1]
                add_simulation_turn(
                    db,
                    sim_id=sim_id,
                    turn_number=data.turn,
                    role=data.role,
                    agent_type=step.agent_type,
                    content=step.output,
                    duration_ms=step.duration_ms,
                )
        complete_simulation(db, sim_id, sim.trace.duration_ms)
    except Exception as e:
        fail_simulation(db, sim_id)
        print(f"    ERROR during simulation: {e}")
        return False

    if evaluate:
        try:
            turns = get_simulation_turns(db, sim_id)
            main_turns = [t for t in turns if t["agent_type"] != "QuizResponse"]
            quiz_turns = [t for t in turns if t["agent_type"] == "QuizResponse"]
            transcript = [{"role": t["role"], "content": t["content"]} for t in main_turns]
            answer_key = scenario.quiz
            quiz_responses = [
                {"question": answer_key[i]["question"], "answer": t["content"]}
                for i, t in enumerate(quiz_turns)
                if i < len(answer_key)
            ]

            j_provider, j_model = parse_provider_model(judge_model)
            judge = JudgeAgent(j_provider, j_model)
            result = await judge.evaluate(
                transcript=transcript,
                quiz_responses=quiz_responses,
                answer_key=answer_key,
                mode=mode,
            )
            delete_evaluation(db, sim_id)
            create_evaluation(db, sim_id, judge_model, result)
            score = result.get("comprehension_score")
            print(f"    Evaluated — comprehension: {score}")
        except Exception as e:
            print(f"    Evaluation failed: {e}")

    return True


def build_existing_set(db: Database) -> set[str]:
    """Return set of 'persona|scenario|style|mode' for all existing simulations."""
    sims = list_simulations(db)
    return {
        f"{s['persona_name']}|{s['scenario_name']}|{s['style']}|{s['mode']}"
        for s in sims
    }


async def async_main(args: argparse.Namespace) -> int:
    judge_model = args.judge_model or args.model

    # Filter conditions
    if args.conditions:
        wanted = set(args.conditions.split(","))
        conditions = [(s, m) for s, m in ALL_CONDITIONS if condition_key(s, m) in wanted]
    else:
        conditions = ALL_CONDITIONS

    # Filter personas
    if args.personas:
        wanted_names = {n.strip() for n in args.personas.split(",")}
        personas = [p for p in PERSONAS if p.name in wanted_names]
    else:
        personas = PERSONAS

    # Filter scenarios
    if args.scenarios:
        wanted_names = {n.strip() for n in args.scenarios.split(",")}
        scenarios = [s for s in SCENARIOS if s.test_name in wanted_names]
    else:
        scenarios = SCENARIOS

    total = len(personas) * len(scenarios) * len(conditions)
    print(f"\nBatch run: {len(personas)} personas × {len(scenarios)} scenarios × {len(conditions)} conditions = {total} runs")
    print(f"  Model: {args.model}")
    if args.evaluate:
        print(f"  Judge: {judge_model}")
    print(f"  Skip existing: {args.skip_existing}")
    print(f"  Dry run: {args.dry_run}")
    print()

    if args.dry_run:
        for persona in personas:
            for scenario in scenarios:
                for style, mode in conditions:
                    print(f"  Would run: {persona.name} | {scenario.test_name} | {style}+{mode}")
        return 0

    db = Database(DB_PATH)
    db.init()

    existing = build_existing_set(db) if args.skip_existing else set()
    skipped = 0
    succeeded = 0
    failed = 0
    start = datetime.now()

    run_num = 0
    for persona in personas:
        for scenario in scenarios:
            for style, mode in conditions:
                run_num += 1
                combo_key = f"{persona.name}|{scenario.test_name}|{style}|{mode}"
                label = f"[{run_num}/{total}] {persona.name} | {scenario.test_name} | {style}+{mode}"

                if args.skip_existing and combo_key in existing:
                    print(f"  SKIP  {label}")
                    skipped += 1
                    continue

                print(f"  RUN   {label}")
                ok = await run_one(
                    db=db,
                    persona=persona,
                    scenario=scenario,
                    style=style,
                    mode=mode,
                    model=args.model,
                    judge_model=judge_model,
                    evaluate=args.evaluate,
                )
                if ok:
                    succeeded += 1
                else:
                    failed += 1

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\n{'='*60}")
    print(f"  Done in {elapsed:.1f}s")
    print(f"  Succeeded: {succeeded}  Failed: {failed}  Skipped: {skipped}")
    print(f"{'='*60}\n")

    db.close()
    return 0 if failed == 0 else 1


def main():
    parser = argparse.ArgumentParser(description="Batch simulation runner")
    parser.add_argument("--model", default="mock:default", help="LLM model for simulations")
    parser.add_argument("--judge-model", default=None, help="LLM model for judge (defaults to --model)")
    parser.add_argument("--evaluate", action="store_true", help="Run judge after each simulation")
    parser.add_argument("--skip-existing", action="store_true", help="Skip already-run combinations")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without running")
    parser.add_argument("--conditions", default=None, help="Comma-separated conditions to run")
    parser.add_argument("--personas", default=None, help="Comma-separated persona names")
    parser.add_argument("--scenarios", default=None, help="Comma-separated scenario names")
    args = parser.parse_args()

    sys.exit(asyncio.run(async_main(args)))


if __name__ == "__main__":
    main()