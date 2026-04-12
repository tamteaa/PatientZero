"""Generic distribution types for declaring agent trait spaces.

A :class:`Distribution` is a DAG of trait nodes. Each node is either a
:class:`Marginal` (unconditioned) or a :class:`Conditional` that depends on
another trait in the same distribution. The DAG is topologically sorted at
construction and sampled in causal order.

Example::

    Distribution(
        age={"young": 0.3, "old": 0.7},
        literacy=Conditional("age", {
            "young": {"low": 0.2, "high": 0.8},
            "old":   {"low": 0.6, "high": 0.4},
        }),
    )
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from functools import cached_property
from typing import Iterable, Iterator, Mapping, Union

Weights = Mapping[str, float]
_WEIGHT_TOLERANCE = 1e-3


# ── Node types ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Marginal:
    """Unconditioned discrete distribution over a single trait."""

    weights: dict[str, float]

    def __post_init__(self) -> None:
        _validate_weights(self.weights)

    def sample(self, rng: random.Random) -> str:
        values = list(self.weights.keys())
        w = list(self.weights.values())
        return rng.choices(values, weights=w, k=1)[0]

    def values(self) -> list[str]:
        return list(self.weights.keys())


@dataclass(frozen=True)
class Conditional:
    """Discrete distribution for one trait conditioned on a sibling trait."""

    parent: str
    table: dict[str, dict[str, float]]

    def __post_init__(self) -> None:
        if not self.table:
            raise ValueError(f"Conditional on {self.parent!r} has empty table")
        for parent_val, child_weights in self.table.items():
            try:
                _validate_weights(child_weights)
            except ValueError as e:
                raise ValueError(
                    f"Conditional[{self.parent}={parent_val!r}]: {e}"
                ) from None

    def sample(self, parent_value: str, rng: random.Random) -> str:
        if parent_value not in self.table:
            raise KeyError(
                f"Conditional on {self.parent!r} has no entry for parent value "
                f"{parent_value!r}. Known: {sorted(self.table)}"
            )
        weights = self.table[parent_value]
        values = list(weights.keys())
        w = list(weights.values())
        return rng.choices(values, weights=w, k=1)[0]

    def values(self) -> list[str]:
        seen: set[str] = set()
        for child_weights in self.table.values():
            seen.update(child_weights.keys())
        return sorted(seen)


Node = Union[Marginal, Conditional]


# ── Top-level distribution ────────────────────────────────────────────────────

class Distribution:
    """DAG of trait nodes.

    Traits are declared as kwargs. Each value is either:

    - a ``dict[str, float]`` (auto-wrapped to :class:`Marginal`),
    - a :class:`Marginal` instance, or
    - a :class:`Conditional` referencing another trait by name.

    The DAG is topo-sorted at construction. Sampling walks topo order, and
    every :class:`Conditional` node reads the already-sampled value of its
    parent. Treat instances as immutable — mutation methods
    (:meth:`replace`, :meth:`reweight`) return new instances.
    """

    __slots__ = ("_nodes", "_topo", "__dict__")

    def __init__(self, **traits: Union[Weights, Marginal, Conditional]) -> None:
        nodes: dict[str, Node] = {}
        for name, spec in traits.items():
            if not name.isidentifier():
                raise ValueError(f"Trait name {name!r} is not a valid identifier")
            if isinstance(spec, Conditional):
                nodes[name] = spec
            elif isinstance(spec, Marginal):
                nodes[name] = spec
            elif isinstance(spec, Mapping):
                nodes[name] = Marginal(dict(spec))
            else:
                raise TypeError(
                    f"Trait {name!r}: expected dict, Marginal, or Conditional, "
                    f"got {type(spec).__name__}"
                )
        self._nodes: dict[str, Node] = nodes
        self._topo: tuple[str, ...] = _topo_sort(nodes)

    # ── Introspection ─────────────────────────────────────────────────────────

    @property
    def traits(self) -> tuple[str, ...]:
        return tuple(self._nodes.keys())

    @property
    def topo_order(self) -> tuple[str, ...]:
        return self._topo

    def node(self, trait: str) -> Node:
        return self._nodes[trait]

    def parents(self, trait: str) -> tuple[str, ...]:
        n = self._nodes[trait]
        return (n.parent,) if isinstance(n, Conditional) else ()

    @cached_property
    def support(self) -> dict[str, list[str]]:
        return {t: self._nodes[t].values() for t in self._topo}

    def __repr__(self) -> str:
        parts = []
        for t in self._topo:
            n = self._nodes[t]
            if isinstance(n, Marginal):
                parts.append(f"{t}={n.values()}")
            else:
                parts.append(f"{t}|{n.parent}")
        return f"Distribution({', '.join(parts)})"

    # ── Sampling ──────────────────────────────────────────────────────────────

    def sample(
        self,
        rng: random.Random | None = None,
        **constraints: str,
    ) -> dict[str, str]:
        """Draw one profile. ``constraints`` pins specific traits to given
        values; downstream conditionals still use the pinned value."""
        r = rng or random.Random()
        self._validate_constraints(constraints)
        out: dict[str, str] = {}
        for trait in self._topo:
            if trait in constraints:
                out[trait] = constraints[trait]
                continue
            node = self._nodes[trait]
            if isinstance(node, Marginal):
                out[trait] = node.sample(r)
            else:
                parent_val = out[node.parent]
                out[trait] = node.sample(parent_val, r)
        return out

    def _validate_constraints(self, constraints: Mapping[str, str]) -> None:
        for trait, value in constraints.items():
            if trait not in self._nodes:
                raise KeyError(
                    f"Constraint on unknown trait {trait!r}. "
                    f"Known: {sorted(self._nodes)}"
                )
            allowed = self.support[trait]
            if value not in allowed:
                raise ValueError(
                    f"Constraint {trait}={value!r} not in support {allowed}"
                )

    # ── Marginalization ───────────────────────────────────────────────────────

    def marginal(self, trait: str) -> Marginal:
        """P(trait) with all ancestors integrated out."""
        if trait not in self._nodes:
            raise KeyError(trait)
        return self._marginal_recursive(trait)

    def _marginal_recursive(self, trait: str) -> Marginal:
        node = self._nodes[trait]
        if isinstance(node, Marginal):
            return Marginal(dict(node.weights))
        parent_marginal = self._marginal_recursive(node.parent)
        out: dict[str, float] = {}
        for pv, pp in parent_marginal.weights.items():
            child_weights = node.table.get(pv, {})
            for cv, cp in child_weights.items():
                out[cv] = out.get(cv, 0.0) + pp * cp
        _renormalize(out)
        return Marginal(out)

    # ── Joint enumeration ────────────────────────────────────────────────────

    def cells(self, *traits: str) -> list[tuple[tuple[str, ...], float]]:
        """Exact joint cells over the DAG.

        Empty ``traits`` enumerates the full joint in ``topo_order``. With a
        subset, returns the exact marginal joint over those traits, sorted by
        descending probability.
        """
        subset: tuple[str, ...] = traits or self._topo
        for t in subset:
            if t not in self._nodes:
                raise KeyError(t)
        projected: dict[tuple[str, ...], float] = {}
        for full_cell, prob in self._enumerate_joint(0, {}, 1.0):
            key = tuple(full_cell[t] for t in subset)
            projected[key] = projected.get(key, 0.0) + prob
        return sorted(projected.items(), key=lambda kv: -kv[1])

    def _enumerate_joint(
        self, depth: int, partial: dict[str, str], prob: float
    ) -> Iterator[tuple[dict[str, str], float]]:
        if depth == len(self._topo):
            yield dict(partial), prob
            return
        trait = self._topo[depth]
        node = self._nodes[trait]
        iterable: Iterable[tuple[str, float]]
        if isinstance(node, Marginal):
            iterable = node.weights.items()
        else:
            iterable = node.table.get(partial[node.parent], {}).items()
        for v, p in iterable:
            if p == 0.0:
                continue
            partial[trait] = v
            yield from self._enumerate_joint(depth + 1, partial, prob * p)
            del partial[trait]

    # ── Mutation (returns new Distribution) ──────────────────────────────────

    def replace(
        self,
        trait: str,
        node: Union[Weights, Marginal, Conditional],
    ) -> "Distribution":
        """Return a new Distribution with ``trait`` replaced by ``node``."""
        if trait not in self._nodes:
            raise KeyError(trait)
        new_traits: dict[str, Node] = dict(self._nodes)
        if isinstance(node, (Marginal, Conditional)):
            new_traits[trait] = node
        elif isinstance(node, Mapping):
            new_traits[trait] = Marginal(dict(node))
        else:
            raise TypeError(
                f"Expected dict, Marginal, or Conditional, got {type(node).__name__}"
            )
        return Distribution(**new_traits)

    def reweight(self, trait: str, weights: Weights) -> "Distribution":
        """Return a new Distribution with ``trait`` replaced by a Marginal
        over ``weights``. Severs parent dependency on ``trait``.

        Raises if ``weights`` introduces values that downstream conditionals
        don't handle.
        """
        if trait not in self._nodes:
            raise KeyError(trait)
        new_values = set(weights.keys())
        for downstream_name, dn in self._nodes.items():
            if not isinstance(dn, Conditional) or dn.parent != trait:
                continue
            missing = new_values - set(dn.table.keys())
            if missing:
                raise ValueError(
                    f"reweight({trait!r}, ...) introduces values {sorted(missing)} "
                    f"not handled by downstream conditional {downstream_name!r}"
                )
        return self.replace(trait, Marginal(dict(weights)))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _validate_weights(weights: Mapping[str, float]) -> None:
    if not weights:
        raise ValueError("weights must be non-empty")
    for v, w in weights.items():
        if w < 0:
            raise ValueError(f"weight for {v!r} is negative: {w}")
    total = sum(weights.values())
    if not math.isclose(total, 1.0, abs_tol=_WEIGHT_TOLERANCE):
        raise ValueError(f"weights must sum to 1.0 (got {total})")


def _renormalize(weights: dict[str, float]) -> None:
    total = sum(weights.values())
    if total == 0:
        return
    for k in list(weights.keys()):
        weights[k] /= total


def _topo_sort(nodes: dict[str, Node]) -> tuple[str, ...]:
    """Stable topo sort: respects declaration order among independent traits.
    Raises on unknown parents, self-loops, or cycles."""
    for name, node in nodes.items():
        if isinstance(node, Conditional):
            if node.parent not in nodes:
                raise ValueError(
                    f"Trait {name!r} depends on unknown parent {node.parent!r}. "
                    f"Known: {sorted(nodes)}"
                )
            if node.parent == name:
                raise ValueError(f"Trait {name!r} depends on itself")

    placed: list[str] = []
    remaining = list(nodes.keys())
    while remaining:
        progress = False
        for name in list(remaining):
            node = nodes[name]
            parent = node.parent if isinstance(node, Conditional) else None
            if parent is None or parent in placed:
                placed.append(name)
                remaining.remove(name)
                progress = True
        if not progress:
            raise ValueError(
                f"Cycle detected in distribution DAG: {sorted(remaining)}"
            )
    return tuple(placed)


def distribution_to_dict(distribution: Distribution) -> dict[str, dict]:
    data: dict[str, dict] = {}
    for trait in distribution.topo_order:
        node = distribution.node(trait)
        if isinstance(node, Marginal):
            data[trait] = {
                "kind": "marginal",
                "weights": dict(node.weights),
            }
        else:
            data[trait] = {
                "kind": "conditional",
                "parent": node.parent,
                "table": {k: dict(v) for k, v in node.table.items()},
            }
    return data


def distribution_from_dict(data: Mapping[str, Mapping]) -> Distribution:
    traits: dict[str, Node] = {}
    for trait, spec in data.items():
        kind = spec.get("kind")
        if kind == "marginal":
            traits[trait] = Marginal(dict(spec["weights"]))
        elif kind == "conditional":
            traits[trait] = Conditional(
                str(spec["parent"]),
                {k: dict(v) for k, v in spec["table"].items()},
            )
        else:
            raise ValueError(f"Unknown distribution node kind for {trait!r}: {kind!r}")
    return Distribution(**traits)


__all__ = [
    "Conditional",
    "Distribution",
    "Marginal",
    "distribution_from_dict",
    "distribution_to_dict",
]
