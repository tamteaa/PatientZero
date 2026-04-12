"""Per-simulation log files under ``logs/<session-ts>/<sim_id>.log``.

One file per simulation, written incrementally as turns execute. Carries
enough context to reproduce or debug a run without touching the DB:
experiment id, optimization target id, model, sampled profiles, rendered
system prompts, every turn (input messages + output + duration), final
state, and the judge evaluation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _indent(text: str, prefix: str = "  ") -> str:
    return "\n".join(prefix + line for line in text.splitlines())


class SimulationLogger:
    """Writes one log file per simulation under a per-process session dir."""

    def __init__(self, base_dir: str = "logs"):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
        self.session_dir = Path(base_dir) / ts
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self._paths: dict[str, Path] = {}

    def _path(self, sim_id: str) -> Path | None:
        return self._paths.get(sim_id)

    # ── Lifecycle ───────────────────────────────────────────────────────────

    def open(
        self,
        sim_id: str,
        *,
        experiment_id: str,
        experiment_name: str,
        optimization_target_id: str,
        model: str,
        max_turns: int,
        profiles: dict[str, dict[str, str]],
        system_prompts: dict[str, str],
    ) -> None:
        exp_dir = self.session_dir / experiment_id
        exp_dir.mkdir(parents=True, exist_ok=True)
        path = exp_dir / f"{sim_id}.log"
        self._paths[sim_id] = path
        with open(path, "w") as f:
            f.write(f"=== Simulation {sim_id} ===\n")
            f.write(f"Experiment: {experiment_name} ({experiment_id})\n")
            f.write(f"Optimization target: {optimization_target_id}\n")
            f.write(f"Model: {model}\n")
            f.write(f"Max turns: {max_turns}\n")
            f.write(f"Started: {_ts()}\n")

            f.write("\n──── Profiles ────\n")
            for agent_name, traits in profiles.items():
                f.write(f"\n[{agent_name}]\n")
                for trait, value in traits.items():
                    if "\n" in str(value):
                        f.write(f"  {trait}: |\n{_indent(str(value), '    ')}\n")
                    else:
                        f.write(f"  {trait}: {value}\n")

            f.write("\n──── System prompts ────\n")
            for agent_name, prompt in system_prompts.items():
                f.write(f"\n[{agent_name}]\n{prompt}\n")

            f.write("\n──── Turns ────\n")

    def log_turn(
        self,
        sim_id: str,
        *,
        turn: int,
        role: str,
        input_messages: list[dict[str, str]],
        output: str,
        duration_ms: float,
    ) -> None:
        path = self._path(sim_id)
        if path is None:
            return
        with open(path, "a") as f:
            f.write(f"\n### Turn {turn + 1} [{role}] {duration_ms:.0f}ms\n")
            f.write("-- input --\n")
            if not input_messages:
                f.write("(no messages)\n")
            for msg in input_messages:
                f.write(f"[{msg['role']}] {msg['content']}\n")
            f.write("-- output --\n")
            f.write(output.rstrip() + "\n")

    def log_evaluation(self, sim_id: str, judge_result: Any) -> None:
        path = self._path(sim_id)
        if path is None:
            return
        with open(path, "a") as f:
            f.write("\n──── Evaluation ────\n")
            f.write(f"Model: {getattr(judge_result, 'model', '?')}\n")
            scores = getattr(judge_result, "scores", {}) or {}
            f.write(f"Scores: {json.dumps(scores)}\n")
            justification = getattr(judge_result, "justification", None)
            if justification:
                f.write(f"Justification: {justification}\n")

    def close(self, sim_id: str, *, state: str, duration_ms: float) -> None:
        path = self._path(sim_id)
        if path is None:
            return
        with open(path, "a") as f:
            f.write("\n──── Final ────\n")
            f.write(f"State: {state}\n")
            f.write(f"Duration: {duration_ms:.0f}ms\n")
            f.write(f"Ended: {_ts()}\n")
