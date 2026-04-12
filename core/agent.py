from __future__ import annotations

import string
from dataclasses import dataclass
from typing import Any

from core.distribution import Distribution


def _parse_prompt_fields(prompt: str) -> frozenset[str]:
    names: set[str] = set()
    for _, field_name, _, _ in string.Formatter().parse(prompt):
        if not field_name:
            continue
        base = field_name.split(".", 1)[0].split("[", 1)[0]
        names.add(base)
    return frozenset(names)


@dataclass(frozen=True)
class Agent:
    """User-facing agent declaration: name, prompt template, trait distribution."""
    name: str
    prompt: str
    distribution: Distribution
    model: str | None = None

    @property
    def prompt_fields(self) -> frozenset[str]:
        return _parse_prompt_fields(self.prompt)

    def render(self, fields: dict[str, Any]) -> str:
        try:
            return self.prompt.format(**fields)
        except KeyError as exc:
            missing = exc.args[0]
            raise ValueError(
                f"Missing field {missing!r} while rendering prompt for agent {self.name!r}"
            ) from exc

    def sample(self, rng=None, **constraints: str) -> dict[str, str]:
        return self.distribution.sample(rng=rng, **constraints)
