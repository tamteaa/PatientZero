from dataclasses import dataclass


@dataclass(frozen=True)
class AppSettings:
    """Defaults are overridden from env in ``core.config.settings``."""

    max_concurrent_simulations: int
    max_concurrent_optimizations: int
