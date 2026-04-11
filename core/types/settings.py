from dataclasses import dataclass


@dataclass(frozen=True)
class AppSettings:
    max_concurrent_simulations: int = 5
    # Default 1: optimize is heavy; raise 409 if a second run starts while one is in flight.
    max_concurrent_optimizations: int = 1
