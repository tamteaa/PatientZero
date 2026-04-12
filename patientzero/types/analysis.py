from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class CoverageReport:
    cells_total: int
    cells_hit: int
    simulations_counted: int
    coverage_pct: float
    estimated_total_needed: int
    target_method: Literal["monte_carlo", "independence"] = "monte_carlo"
    mc_samples: int | None = None
    distribution_match: float | None = None

    def to_dict(self) -> dict:
        return {
            "cells_total": self.cells_total,
            "cells_hit": self.cells_hit,
            "simulations_counted": self.simulations_counted,
            "coverage_pct": self.coverage_pct,
            "estimated_total_needed": self.estimated_total_needed,
            "target_method": self.target_method,
            "mc_samples": self.mc_samples,
            "distribution_match": self.distribution_match,
        }
