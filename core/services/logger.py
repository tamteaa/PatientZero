from datetime import datetime, timezone
from pathlib import Path


class SimulationLogger:
    """Writes plain-text log files for each simulation, grouped by server session."""

    def __init__(self, base_dir: str = "logs"):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
        self.session_dir = Path(base_dir) / ts
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self._logs: dict[str, Path] = {}

    def start(self, sim_id: str, metadata: dict[str, str]) -> None:
        sim_dir = self.session_dir / sim_id
        sim_dir.mkdir(parents=True, exist_ok=True)
        path = sim_dir / "simulation.log"
        self._logs[sim_id] = path
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        with open(path, "w") as f:
            f.write(f"=== Simulation {sim_id} ===\n")
            f.write(f"Time: {ts}\n")
            for k, v in metadata.items():
                f.write(f"{k}: {v}\n")
            f.write("\n")

    def log_turn(self, sim_id: str, turn: int, role: str, content: str, duration_ms: float) -> None:
        path = self._logs.get(sim_id)
        if not path:
            return
        with open(path, "a") as f:
            f.write(f"--- Turn {turn + 1} [{role}] ({duration_ms:.0f}ms) ---\n")
            f.write(content)
            f.write("\n\n")

    def log_turn_detail(
        self, sim_id: str, turn: int, role: str,
        system_prompt: str, messages: list[dict], output: str, duration_ms: float,
    ) -> None:
        sim_dir = self._logs.get(sim_id)
        if not sim_dir:
            return
        path = sim_dir.parent / f"turn_{turn + 1}_{role}.log"
        with open(path, "w") as f:
            f.write(f"=== Turn {turn + 1} [{role}] ({duration_ms:.0f}ms) ===\n\n")
            f.write("## System Prompt\n")
            f.write(system_prompt)
            f.write("\n\n## Messages\n")
            for msg in messages:
                f.write(f"[{msg['role']}]\n{msg['content']}\n\n")
            f.write("## Output\n")
            f.write(output)
            f.write("\n")
