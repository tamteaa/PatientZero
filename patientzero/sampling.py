"""Deterministic RNG streams for reproducible profile sampling."""

import hashlib
import random


def stable_rng(seed: int, draw_index: int) -> random.Random:
    """Process-stable RNG for experiment draw ``draw_index`` under integer ``seed``."""
    digest = hashlib.sha256(f"{seed}\x00{draw_index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "little"))
