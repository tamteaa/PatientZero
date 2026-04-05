from dataclasses import dataclass


@dataclass
class TurnStartEvent:
    role: str     # "doctor" | "patient"
    turn: int     # 0-based index


@dataclass
class TurnEndEvent:
    role: str     # "doctor" | "patient"
    turn: int
