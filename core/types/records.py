from dataclasses import dataclass, asdict, field

from core.types.distribution import DoctorDistribution, PatientDistribution
from core.types.judge_result import JudgeResult


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


@dataclass
class ExperimentRecord:
    id: str
    name: str
    created_at: str
    patient_distribution: PatientDistribution
    doctor_distribution: DoctorDistribution
    current_optimization_target_id: str | None
    sampling_seed: int | None = None
    sample_draw_index: int = 0

    def to_summary_dict(self) -> dict:
        """Shallow representation — skips the heavy distributions."""
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
            "current_optimization_target_id": self.current_optimization_target_id,
            "sampling_seed": self.sampling_seed,
        }

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
            "current_optimization_target_id": self.current_optimization_target_id,
            "sampling_seed": self.sampling_seed,
            "sample_draw_index": self.sample_draw_index,
            "patient_distribution": asdict(self.patient_distribution),
            "doctor_distribution": asdict(self.doctor_distribution),
        }


@dataclass
class SimulationRecord:
    id: str
    experiment_id: str
    persona_name: str
    scenario_name: str
    model: str
    state: str
    config_json: str
    duration_ms: float | None
    created_at: str
    completed_at: str | None
    style: str | None = None
    optimization_target_id: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
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
    created_at: str | None
    judge_results: list[JudgeResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "simulation_id": self.simulation_id,
            "created_at": self.created_at,
            "judge_results": [j.to_dict() for j in self.judge_results],
        }
