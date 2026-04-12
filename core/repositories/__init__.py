"""
core.repositories — the single persistence layer.

Import `RepoSet` and construct one per `Database`. Services take a
RepoSet (or individual repos) via constructor; routes pull the shared
RepoSet from `backend.api.dependencies`.
"""

from dataclasses import dataclass

from core.db.database import Database
from core.repositories.base import BaseRepository
from core.repositories.evaluations import EvaluationRepository
from core.repositories.experiments import ExperimentRepository
from core.repositories.optimization_targets import OptimizationTargetRepository
from core.repositories.simulations import SimulationRepository


@dataclass
class RepoSet:
    """Bundle of all repositories backed by one Database."""
    experiments: ExperimentRepository
    simulations: SimulationRepository
    evaluations: EvaluationRepository
    optimization_targets: OptimizationTargetRepository

    @classmethod
    def for_db(cls, db: Database) -> "RepoSet":
        return cls(
            experiments=ExperimentRepository(db),
            simulations=SimulationRepository(db),
            evaluations=EvaluationRepository(db),
            optimization_targets=OptimizationTargetRepository(db),
        )


__all__ = [
    "BaseRepository",
    "ExperimentRepository",
    "SimulationRepository",
    "EvaluationRepository",
    "OptimizationTargetRepository",
    "RepoSet",
]
