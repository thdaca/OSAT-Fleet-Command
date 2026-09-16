"""Offline declared-unit validation for Step01 physical-relation records.

Pint is imported only when these research/audit helpers are called.  Canonical
telemetry unit strings stored in Step01 records are never rewritten.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .schema import PhysicsRelation, ResearchCandidate


CANONICAL_UNIT_ALIASES: dict[str, str] = {
    "RPM": "revolution / minute",
    "A/RPM": "ampere * minute / revolution",
}
INTENTIONALLY_NONPHYSICAL_UNITS: dict[str, str] = {
    "state": "Categorical equipment or cycle state; not a physical quantity.",
}


class PhysicsUnitDependencyError(RuntimeError):
    """Pint is unavailable for an explicitly requested offline unit audit."""


def canonical_unit_expression(unit: str) -> str:
    """Map a repository spelling to one deterministic Pint expression."""

    if unit in INTENTIONALLY_NONPHYSICAL_UNITS:
        return unit
    return CANONICAL_UNIT_ALIASES.get(unit, unit)


def _unit_registry() -> Any:
    try:
        import pint
    except ImportError as exc:
        raise PhysicsUnitDependencyError(
            "Pint is required only for offline Step01 dimensional audits"
        ) from exc
    return pint.UnitRegistry()


def declared_unit_dimension(unit: str) -> str:
    """Return a Pint dimensionality or the documented metadata classification."""

    if unit in INTENTIONALLY_NONPHYSICAL_UNITS:
        return "NONPHYSICAL_METADATA"
    registry = _unit_registry()
    return str(registry.parse_units(canonical_unit_expression(unit)).dimensionality)


def assert_compatible_units(first: str, second: str) -> None:
    """Raise ValueError when two declared physical units are incompatible."""

    if first in INTENTIONALLY_NONPHYSICAL_UNITS or second in INTENTIONALLY_NONPHYSICAL_UNITS:
        if first == second:
            return
        raise ValueError("Physical units and nonphysical metadata are not compatible")
    registry = _unit_registry()
    first_unit = registry.parse_units(canonical_unit_expression(first))
    second_unit = registry.parse_units(canonical_unit_expression(second))
    if first_unit.dimensionality != second_unit.dimensionality:
        raise ValueError(f"Incompatible dimensions: {first!r} and {second!r}")


def _declared_units(
    relations: Iterable[PhysicsRelation],
    candidates: Iterable[ResearchCandidate],
) -> tuple[str, ...]:
    units: list[str] = []
    for relation in relations:
        units.extend(unit for _, unit in relation.expected_units)
        units.extend(requirement.required_unit for requirement in relation.measurement_requirements)
        units.extend(parameter.unit for parameter in relation.parameter_specs)
        units.append(relation.output_unit)
    for candidate in candidates:
        units.extend(requirement.required_unit for requirement in candidate.measurement_requirements)
    return tuple(units)


def audit_declared_units(
    relations: Iterable[PhysicsRelation],
    candidates: Iterable[ResearchCandidate],
) -> tuple[str, ...]:
    """Audit parsing and the fixed spindle relation's declared dimensions."""

    relation_records = tuple(relations)
    candidate_records = tuple(candidates)
    issues: list[str] = []
    for unit in sorted(set(_declared_units(relation_records, candidate_records))):
        if unit in INTENTIONALLY_NONPHYSICAL_UNITS:
            continue
        try:
            declared_unit_dimension(unit)
        except Exception as exc:
            issues.append(f"Unit {unit!r} is not parseable by Pint: {exc}")
    for relation in relation_records:
        if relation.relation_id != "spindle.current_speed_residual":
            continue
        expected = dict(relation.expected_units)
        try:
            assert_compatible_units(expected["spindle_current"], relation.output_unit)
            registry = _unit_registry()
            slope = registry.parse_units(canonical_unit_expression("A/RPM"))
            speed = registry.parse_units(canonical_unit_expression(expected["spindle_speed"]))
            current = registry.parse_units(canonical_unit_expression(expected["spindle_current"]))
            if (slope * speed).dimensionality != current.dimensionality:
                issues.append("Spindle slope multiplied by speed is not current-dimensional")
        except Exception as exc:
            issues.append(f"Spindle relation dimensional audit failed: {exc}")
    return tuple(issues)

