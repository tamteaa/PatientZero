import argparse
import csv
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path
import os

from dotenv import dotenv_values, load_dotenv
from core.agents.judge import JudgeAgent
from core.agents.prompts import build_doctor_prompt, build_patient_prompt
from core.agents.sim_agent import SimAgent
from core.config.settings import DB_PATH
from core.db.database import Database
from core.db.queries.evaluations import create_evaluation, delete_evaluation
from core.db.queries.experiments import get_experiment
from core.db.queries.simulations import (
    create_simulation,
    fail_simulation,
    get_simulation,
    get_simulation_turns,
)
from core.generators.profile import StaticDoctorGenerator, StaticPatientGenerator
from core.generators.static import StaticScenarioGenerator
from core.llm.factory import parse_provider_model
from core.simulation.simulation import Simulation
from core.types import Message, Transcript

METRICS = [
    "comprehension_score",
    "factual_recall",
    "applied_reasoning",
    "explanation_quality",
    "interaction_quality",
]


def _analysis_rows(db: Database) -> list[dict]:
    raw = db.conn.execute(
        """
        SELECT
            e.judge_results_json,
            s.persona_name, s.scenario_name, s.config_json
        FROM evaluations e
        JOIN simulations s ON s.id = e.simulation_id
        WHERE s.state = 'completed'
        ORDER BY e.created_at DESC
        """
    ).fetchall()
    rows = []
    for r in raw:
        row = dict(r)
        judge_results = json.loads(row.pop("judge_results_json", "[]") or "[]")
        for metric in METRICS:
            vals = [j.get(metric) for j in judge_results if j.get(metric) is not None]
            row[metric] = sum(vals) / len(vals) if vals else None
        gaps = [
            j.get("confidence_comprehension_gap")
            for j in judge_results
            if j.get("confidence_comprehension_gap")
        ]
        row["confidence_comprehension_gap"] = gaps[0] if gaps else None
        cfg = json.loads(row.pop("config_json", "{}"))
        row["experiment_id"] = cfg.get("batch_id") or cfg.get("experiment_id")
        row["optimization_target_id"] = cfg.get("optimization_target_id")
        row["policy_version"] = cfg.get("policy_version")
        row["style"] = cfg.get("style")
        pt = cfg.get("patient", {}).get("traits", {})
        dt = cfg.get("doctor", {}).get("traits", {})
        row["patient_literacy"] = pt.get("literacy")
        row["patient_anxiety"] = pt.get("anxiety")
        row["patient_tendency"] = pt.get("tendency")
        row["patient_age"] = pt.get("age")
        row["patient_education"] = pt.get("education")
        row["doctor_empathy"] = dt.get("empathy")
        row["doctor_verbosity"] = dt.get("verbosity")
        row["doctor_comp_check"] = dt.get("comprehension_checking")
        row["doctor_time_pressure"] = dt.get("time_pressure")
        rows.append(row)
    return rows


def _summary(rows: list[dict]) -> dict:
    if not rows:
        return {"total_evaluations": 0, "overall": {}, "worst_combinations": [], "gap_analysis": {"gap_rate": 0.0}}
    overall = {}
    for metric in METRICS:
        vals = [r[metric] for r in rows if r.get(metric) is not None]
        overall[metric] = {"mean": round(sum(vals) / len(vals), 2) if vals else None, "n": len(vals)}
    with_gap = [r for r in rows if r.get("confidence_comprehension_gap")]
    combos = {}
    for r in rows:
        k = (
            r.get("patient_literacy"),
            r.get("doctor_empathy"),
            r.get("doctor_verbosity"),
            r.get("scenario_name"),
        )
        combos.setdefault(k, []).append(r)
    worst = []
    for (lit, emp, verb, scen), grp in combos.items():
        vals = [g["comprehension_score"] for g in grp if g.get("comprehension_score") is not None]
        if vals:
            worst.append({
                "patient_literacy": lit,
                "doctor_empathy": emp,
                "doctor_verbosity": verb,
                "scenario": scen,
                "mean_comprehension": round(sum(vals) / len(vals), 1),
                "n": len(vals),
            })
    worst.sort(key=lambda x: x["mean_comprehension"])
    return {
        "total_evaluations": len(rows),
        "overall": overall,
        "gap_analysis": {"gap_rate": round((len(with_gap) / len(rows)) * 100, 1)},
        "worst_combinations": worst[:10],
    }


def start_batch(
    db: Database,
    n_runs: int,
    model: str,
    max_turns: int,
    experiment_db_id: str,
    batch_id: str,
    policy_version: str,
    style: str,
    patient_literacy: str | None = None,
    patient_anxiety: str | None = None,
    doctor_empathy: str | None = None,
    doctor_verbosity: str | None = None,
    sim_timeout_s: int = 180,
):
    exp = get_experiment(db, experiment_db_id)
    if not exp:
        raise ValueError(f"Experiment not found: {experiment_db_id}")

    sim_ids = []
    provider, model_name = parse_provider_model(model)
    patient_gen = StaticPatientGenerator(distribution=exp.patient_distribution)
    doctor_gen = StaticDoctorGenerator(distribution=exp.doctor_distribution)
    scenario_gen = StaticScenarioGenerator()
    for _ in range(n_runs):
        doctor_profile = doctor_gen.generate(n=1, empathy=doctor_empathy, verbosity=doctor_verbosity)[0]
        patient_profile = patient_gen.generate(n=1, literacy=patient_literacy, anxiety=patient_anxiety)[0]
        scenario = scenario_gen.generate(n=1)[0]

        sim_record = create_simulation(
            db=db,
            experiment_id=experiment_db_id,
            persona_name=patient_profile.name,
            scenario_name=scenario.name,
            model=model,
            config={
                "doctor": asdict(doctor_profile),
                "patient": asdict(patient_profile),
                "scenario": asdict(scenario),
                "model": model,
                "style": style,
                "policy_version": policy_version,
                "batch_id": batch_id,
                "optimization_target_id": exp.current_optimization_target_id,
            },
        )

        doctor = SimAgent(
            provider,
            model_name,
            doctor_profile,
            build_doctor_prompt(doctor_profile, scenario, style=style, policy_version=policy_version),
        )
        patient = SimAgent(
            provider,
            model_name,
            patient_profile,
            build_patient_prompt(patient_profile),
        )
        sim = Simulation(db, sim_record.id, doctor, patient, max_turns=max_turns, logger=None)

        import asyncio
        try:
            asyncio.run(asyncio.wait_for(sim.run(), timeout=sim_timeout_s))
        except TimeoutError:
            # wait_for cancels the task; DB may still be `running` unless Simulation cleans up.
            fail_simulation(db, sim_record.id)
        sim_ids.append(sim_record.id)
    return sim_ids


def wait_for_completion(db: Database, sim_ids: list[str], timeout_s: int = 600):
    deadline = time.time() + timeout_s
    pending = set(sim_ids)
    completed: list[str] = []
    errored: list[str] = []
    while pending and time.time() < deadline:
        for sim_id in list(pending):
            sim = get_simulation(db, sim_id)
            if not sim:
                continue
            if sim.state == "completed":
                completed.append(sim_id)
                pending.remove(sim_id)
            elif sim.state == "error":
                errored.append(sim_id)
                pending.remove(sim_id)
        if pending:
            time.sleep(2)
    return completed, errored, list(pending)


async def evaluate_completed(db: Database, sim_ids: list[str], judge_model: str):
    provider, model = parse_provider_model(judge_model)
    judge = JudgeAgent(provider, model)
    evaluated: list[str] = []
    failed: list[str] = []
    for sim_id in sim_ids:
        turns = get_simulation_turns(db, sim_id)
        transcript = Transcript(messages=[Message(role=t.role, content=t.content) for t in turns])
        try:
            result = await judge.evaluate(transcript)
            delete_evaluation(db, sim_id)
            create_evaluation(db, sim_id, result)
            evaluated.append(sim_id)
        except Exception:
            failed.append(sim_id)
    return {"evaluated": evaluated, "failed": failed}


def save_artifacts(db: Database, output_dir: Path, batch_id: str):
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = _analysis_rows(db)
    analysis = _summary(rows)

    all_csv_cols = [
        "persona_name", "scenario_name",
        "patient_literacy", "patient_anxiety", "patient_tendency",
        "patient_age", "patient_education",
        "doctor_empathy", "doctor_verbosity", "doctor_comp_check", "doctor_time_pressure",
        "style", "policy_version", "experiment_id", "optimization_target_id",
        "comprehension_score", "factual_recall", "applied_reasoning",
        "explanation_quality", "interaction_quality", "confidence_comprehension_gap",
    ]
    csv_path = output_dir / "analysis.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_csv_cols)
        writer.writeheader()
        writer.writerows(rows)

    exp_rows = [r for r in rows if r.get("experiment_id") == batch_id]
    if exp_rows:
        with (output_dir / "analysis_experiment.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=all_csv_cols)
            writer.writeheader()
            writer.writerows(exp_rows)

    (output_dir / "analysis.json").write_text(json.dumps(analysis, indent=2), encoding="utf-8")
    return analysis


def main():
    load_dotenv()
    if not os.environ.get("KIMI_API_KEY", "").strip():
        fallback = dotenv_values(".env.example").get("KIMI_API_KEY")
        if fallback and fallback.strip() != "your_kimi_api_key_here":
            os.environ["KIMI_API_KEY"] = fallback
    if "kimi:" in " ".join(sys.argv) and not os.environ.get("KIMI_API_KEY", "").strip():
        raise ValueError("KIMI_API_KEY is required for kimi runs. Set it in .env.")

    parser = argparse.ArgumentParser(description="Run a feedback-loop batch cycle")
    parser.add_argument("--model", default="kimi:kimi-k2.5")
    parser.add_argument("--judge-model", default="kimi:kimi-k2.5")
    parser.add_argument("--n-runs", type=int, default=10)
    parser.add_argument("--max-turns", type=int, default=8)
    parser.add_argument("--style", default="clinical")
    parser.add_argument("--policy-version", default="baseline")
    parser.add_argument(
        "--experiment-db-id",
        required=True,
        help="UUID of a row in experiments (POST /api/experiments). Required DB FK for simulations.",
    )
    parser.add_argument(
        "--batch-id",
        default=None,
        help="Feedback batch label for artifacts and /api/analysis/compare (stored as config_json.batch_id).",
    )
    parser.add_argument(
        "--experiment-id",
        default=None,
        help="Deprecated alias for --batch-id.",
    )
    parser.add_argument("--patient-literacy", default=None)
    parser.add_argument("--patient-anxiety", default=None)
    parser.add_argument("--doctor-empathy", default=None)
    parser.add_argument("--doctor-verbosity", default=None)
    parser.add_argument("--sim-timeout-s", type=int, default=300)
    parser.add_argument("--timeout-s", type=int, default=600)
    parser.add_argument("--output-root", default="evaluations/feedback/artifacts")
    args = parser.parse_args()

    if args.n_runs < 1 or args.n_runs > 100:
        raise ValueError("n-runs must be between 1 and 100")
    if args.max_turns < 1 or args.max_turns > 50:
        raise ValueError("max-turns must be between 1 and 50")

    batch_id = args.batch_id or args.experiment_id
    if not batch_id:
        raise ValueError("Provide --batch-id (or deprecated --experiment-id) for feedback batch labeling.")

    output_dir = Path(args.output_root) / batch_id
    db = Database(DB_PATH)
    db.init()
    sim_ids = start_batch(
        db=db,
        n_runs=args.n_runs,
        model=args.model,
        max_turns=args.max_turns,
        experiment_db_id=args.experiment_db_id,
        batch_id=batch_id,
        policy_version=args.policy_version,
        style=args.style,
        patient_literacy=args.patient_literacy,
        patient_anxiety=args.patient_anxiety,
        doctor_empathy=args.doctor_empathy,
        doctor_verbosity=args.doctor_verbosity,
        sim_timeout_s=args.sim_timeout_s,
    )
    completed, errored, timed_out = wait_for_completion(db, sim_ids, timeout_s=args.timeout_s)
    import asyncio
    eval_results = asyncio.run(evaluate_completed(db, completed, args.judge_model))
    analysis = save_artifacts(db, output_dir, batch_id)
    db.close()

    summary = {
        "experiment_db_id": args.experiment_db_id,
        "batch_id": batch_id,
        "policy_version": args.policy_version,
        "n_requested": args.n_runs,
        "n_completed": len(completed),
        "n_errored": len(errored),
        "n_timed_out": len(timed_out),
        "n_evaluated": len(eval_results["evaluated"]),
        "n_evaluation_failed": len(eval_results["failed"]),
        "overall_comprehension_mean": (
            analysis.get("overall", {})
            .get("comprehension_score", {})
            .get("mean")
        ),
        "overall_gap_rate": (
            analysis.get("gap_analysis", {})
            .get("gap_rate")
        ),
        "artifacts_dir": str(output_dir),
    }
    (output_dir / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
