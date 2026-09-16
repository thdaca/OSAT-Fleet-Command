"""Optional offline symbolic and experiment-design helpers for Step01."""

from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np


class PhysicsResearchDependencyError(RuntimeError):
    """An optional offline physics-research dependency is unavailable."""


def deterministic_factorial_design(
    factors: Mapping[str, Sequence[float]],
) -> tuple[tuple[str, ...], np.ndarray]:
    """Translate explicit factor levels into a deterministic full-factorial matrix.

    The returned matrix is a research planning aid only.  It does not create
    validation evidence or change any existing :class:`ExperimentPlan` claim.
    """

    try:
        from pydoe import fullfact
    except ImportError as exc:
        raise PhysicsResearchDependencyError(
            "pydoe is required only for offline Step01 experiment planning"
        ) from exc
    names = tuple(factors)
    if not names:
        raise ValueError("At least one explicitly defined factor is required")
    levels = tuple(tuple(float(value) for value in factors[name]) for name in names)
    if any(len(values) < 2 for values in levels):
        raise ValueError("Every factor must define at least two levels")
    if any(not np.all(np.isfinite(values)) for values in levels):
        raise ValueError("Factor levels must be finite")
    indices = np.asarray(fullfact([len(values) for values in levels]), dtype=int)
    matrix = np.empty(indices.shape, dtype=float)
    for column, values in enumerate(levels):
        matrix[:, column] = np.asarray(values, dtype=float)[indices[:, column]]
    return names, matrix


def spindle_residual_symbolic_identity_holds() -> bool:
    """Check the fixed residual algebra offline without evaluating equation text."""

    try:
        from sympy import simplify, symbols
    except ImportError as exc:
        raise PhysicsResearchDependencyError(
            "SymPy is required only for offline Step01 symbolic checks"
        ) from exc
    measured, slope, speed, intercept = symbols("measured slope speed intercept")
    implemented_form = measured - (intercept + slope * speed)
    expanded_form = measured - intercept - slope * speed
    return bool(simplify(implemented_form - expanded_form) == 0)

