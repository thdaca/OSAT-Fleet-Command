"""Step 01: the small reviewed engineering-relation library."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

import numpy as np
from sklearn.linear_model import HuberRegressor


AlignedSignals = Mapping[str, np.ndarray]
RelationCompute = Callable[[AlignedSignals, Mapping[str, float]], Mapping[str, float]]
RelationFit = Callable[[AlignedSignals], Mapping[str, float]]


@dataclass(frozen=True)
class PhysicsRelation:
    relation_id: str
    machine_families: frozenset[str]
    subsystem: str
    required_channels: tuple[str, ...]
    expected_units: tuple[tuple[str, str], ...]
    compute: RelationCompute
    fit: RelationFit | None
    description: str
    equation: str
    assumptions: tuple[str, ...]


def _pressure_flow(
    signals: AlignedSignals, _: Mapping[str, float]
) -> Mapping[str, float]:
    flow = float(np.median(signals["coolant_flow"]))
    if abs(flow) < 1e-12:
        return {}
    pressure = float(np.median(signals["coolant_pressure"]))
    return {"cooling.pressure_flow_ratio": pressure / flow}


def _contact_power(
    signals: AlignedSignals, _: Mapping[str, float]
) -> Mapping[str, float]:
    return {
        "contacts.power_proxy_mw.median": float(
            np.median(signals["contact_voltage_drop"] * signals["site_current"])
        )
    }


def _fit_current_speed(signals: AlignedSignals) -> Mapping[str, float]:
    speed_offset = float(np.median(signals["spindle_speed"]))
    speed = (signals["spindle_speed"] - speed_offset).reshape(-1, 1)
    current = signals["spindle_current"]
    model = HuberRegressor().fit(speed, current)
    slope = float(np.asarray(model.coef_).reshape(-1)[0])
    return {
        "slope": slope,
        "intercept": float(np.asarray(model.intercept_).reshape(-1)[0]) - slope * speed_offset,
    }


def _current_speed_residual(
    signals: AlignedSignals, parameters: Mapping[str, float]
) -> Mapping[str, float]:
    if "slope" not in parameters or "intercept" not in parameters:
        return {}
    expected = parameters["intercept"] + parameters["slope"] * signals["spindle_speed"]
    residual = signals["spindle_current"] - expected
    return {"spindle.current_speed_residual.median": float(np.median(residual))}


PHYSICS_RELATIONS: tuple[PhysicsRelation, ...] = (
    PhysicsRelation(
        relation_id="cooling.pressure_flow",
        machine_families=frozenset({"wafer_saw"}),
        subsystem="cooling",
        required_channels=("coolant_pressure", "coolant_flow"),
        expected_units=(("coolant_pressure", "MPa"), ("coolant_flow", "L/min")),
        compute=_pressure_flow,
        fit=None,
        description="Coolant pressure-to-flow engineering ratio.",
        equation="median(pressure) / median(flow)",
        assumptions=("Signals describe the same coolant branch.",),
    ),
    PhysicsRelation(
        relation_id="contacts.power",
        machine_families=frozenset({"final_test"}),
        subsystem="contacts",
        required_channels=("contact_voltage_drop", "site_current"),
        expected_units=(("contact_voltage_drop", "mV"), ("site_current", "A")),
        compute=_contact_power,
        fit=None,
        description="Contact-path dissipation proxy.",
        equation="voltage_drop[mV] × aligned current[A]",
        assumptions=("Signals refer to the same active contact interval.",),
    ),
    PhysicsRelation(
        relation_id="spindle.current_speed_residual",
        machine_families=frozenset({"wafer_saw", "singulation"}),
        subsystem="spindle",
        required_channels=("spindle_current", "spindle_speed"),
        expected_units=(("spindle_current", "A"), ("spindle_speed", "RPM")),
        compute=_current_speed_residual,
        fit=_fit_current_speed,
        description="Exact-machine spindle current/speed residual.",
        equation="current - (machine_intercept + machine_slope × speed)",
        assumptions=("Fit uses confirmed healthy data from the exact machine.",),
    ),
)


def relations_for_family(family: str) -> tuple[PhysicsRelation, ...]:
    return tuple(
        relation for relation in PHYSICS_RELATIONS if family in relation.machine_families
    )
