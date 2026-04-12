"""
Persisted records and their nested configs.

Two `*Config` dataclasses (`ExperimentConfig`, `SimulationConfig`) describe
the *input* to an experiment or simulation — everything a user declares or
the service seals before a run starts.

Two `*Record` dataclasses (`ExperimentRecord`, `SimulationRecord`) wrap a
config with identity (id, timestamps) and live state (pointers, status).
Records embed their config; repositories serialize the config into a single
JSON column.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from core.agent import Agent
from core.distribution import distribution_from_dict, distribution_to_dict
from core.types.judge_result import JudgeResult


# ── Config (inputs) ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class JudgeConfig:
    """Data-only judge declaration — rubric, instructions, optional model."""
    rubric: dict[str, str]
    instructions: str
    model: str | None = None

    def to_dict(self) -> dict:
        return {"rubric": dict(self.rubric), "instructions": self.instructions, "model": self.model}

    @classmethod
    def from_dict(cls, d: dict) -> "JudgeConfig":
        return cls(
            rubric=dict(d["rubric"]),
            instructions=d["instructions"],
            model=d.get("model"),
        )


@dataclass(frozen=True)
class ExperimentConfig:
    """Everything needed to declare an experiment. The one user-facing input."""
    name: str
    agents: tuple[Agent, ...]
    judge: JudgeConfig
    model: str
    seed: int | None = None
    max_turns: int = 8
    num_optimizations: int = 0

    def __post_init__(self) -> None:
        if not self.agents:
            raise ValueError("ExperimentConfig.agents must be non-empty")
        names = [a.name for a in self.agents]
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate agent names: {names}")
        union: set[str] = set()
        for a in self.agents:
            union.update(a.distribution.support.keys())
        for a in self.agents:
            missing = a.prompt_fields - union
            if missing:
                raise ValueError(
                    f"Agent {a.name!r} prompt references fields {sorted(missing)} "
                    f"not in any agent's distribution"
                )

    def agent(self, name: str) -> Agent:
        for a in self.agents:
            if a.name == name:
                return a
        raise KeyError(name)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "agents": [
                {
                    "name": a.name,
                    "prompt": a.prompt,
                    "distribution": distribution_to_dict(a.distribution),
                    "model": a.model,
                }
                for a in self.agents
            ],
            "judge": self.judge.to_dict(),
            "model": self.model,
            "seed": self.seed,
            "max_turns": self.max_turns,
            "num_optimizations": self.num_optimizations,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ExperimentConfig":
        return cls(
            name=d["name"],
            agents=tuple(
                Agent(
                    name=a["name"],
                    prompt=a["prompt"],
                    distribution=distribution_from_dict(a["distribution"]),
                    model=a.get("model"),
                )
                for a in d["agents"]
            ),
            judge=JudgeConfig.from_dict(d["judge"]),
            model=d["model"],
            seed=d.get("seed"),
            max_turns=int(d.get("max_turns", 8)),
            num_optimizations=int(d.get("num_optimizations", 0)),
        )


@dataclass(frozen=True)
class SimulationConfig:
    """Sealed input to one simulation — enough to replay it."""
    experiment_id: str
    optimization_target_id: str
    profiles: dict[str, dict[str, str]]
    model: str
    max_turns: int
    draw_index: int | None

    def to_dict(self) -> dict:
        return {
            "experiment_id": self.experiment_id,
            "optimization_target_id": self.optimization_target_id,
            "profiles": {k: dict(v) for k, v in self.profiles.items()},
            "model": self.model,
            "max_turns": self.max_turns,
            "draw_index": self.draw_index,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SimulationConfig":
        return cls(
            experiment_id=d["experiment_id"],
            optimization_target_id=d["optimization_target_id"],
            profiles={k: dict(v) for k, v in d["profiles"].items()},
            model=d["model"],
            max_turns=int(d["max_turns"]),
            draw_index=d.get("draw_index"),
        )


# ── Records (persisted) ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class ExperimentRecord:
    id: str
    created_at: str
    config: ExperimentConfig
    current_optimization_target_id: str | None
    sample_draw_index: int = 0

    def to_dict(self, counts: dict[str, int] | None = None) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "config": self.config.to_dict(),
            "current_optimization_target_id": self.current_optimization_target_id,
            "sample_draw_index": self.sample_draw_index,
            "counts": counts or {
                "total": 0,
                "completed": 0,
                "running": 0,
                "error": 0,
                "evaluated": 0,
            },
        }


@dataclass(frozen=True)
class SimulationRecord:
    id: str
    created_at: str
    config: SimulationConfig
    state: str
    duration_ms: float | None
    completed_at: str | None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "config": self.config.to_dict(),
            "state": self.state,
            "duration_ms": self.duration_ms,
            "completed_at": self.completed_at,
        }


@dataclass(frozen=True)
class SimulationTurnRecord:
    id: int
    simulation_id: str
    turn_number: int
    role: str
    agent_type: str
    content: str
    duration_ms: float
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class EvaluationRecord:
    id: int | None
    simulation_id: str
    experiment_id: str | None
    created_at: str | None
    judge_results: list[JudgeResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "simulation_id": self.simulation_id,
            "experiment_id": self.experiment_id,
            "created_at": self.created_at,
            "judge_results": [j.to_dict() for j in self.judge_results],
        }


# ── Session/Turn (chat UI — separate aggregate, kept for compatibility) ──────


@dataclass
class SessionRecord:
    id: str
    title: str
    model: str
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TurnRecord:
    id: int
    session_id: str
    role: str
    content: str
    turn_number: int
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)
