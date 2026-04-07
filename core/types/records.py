from dataclasses import dataclass, asdict


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
class SimulationRecord:
    id: str
    persona_name: str
    scenario_name: str
    style: str
    model: str
    state: str
    config_json: str
    duration_ms: float | None
    created_at: str
    completed_at: str | None

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
    id: int
    simulation_id: str
    model: str
    comprehension_score: float | None
    factual_recall: float | None
    applied_reasoning: float | None
    explanation_quality: float | None
    interaction_quality: float | None
    confidence_comprehension_gap: str | None
    justification: str | None
    created_at: str
    persona_name: str | None = None
    scenario_name: str | None = None
    style: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)
