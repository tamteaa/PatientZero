from dataclasses import dataclass


@dataclass(frozen=True)
class AppSettings:
    max_concurrent_simulations: int = 5
