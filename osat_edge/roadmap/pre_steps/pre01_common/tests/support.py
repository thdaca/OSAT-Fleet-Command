from __future__ import annotations

import datetime as dt
from dataclasses import replace

import numpy as np

from osat_edge.roadmap.pre_steps.pre01_common.pre01_common import (
    ChannelWindow,
    DataOrigin,
    EquipmentState,
    MachineIdentity,
)
from osat_edge.roadmap.pre_steps.pre02_machine_registry.pre02_machine_registry import STATIONS
from osat_edge.roadmap.steps.step02_physical_features.step02_physical_features import Feature, FeatureSet
from osat_edge.roadmap.steps.step04_family_data.step04_family_data import FamilyDataset, FamilySample, ObservedEvent
from osat_edge.roadmap.steps.step07_machine_model.step07_machine_model import FeatureDeviation, MachineModelResult
from osat_edge.roadmap.steps.step08_live_telemetry.step08_live_telemetry import TelemetryStatus


NOW = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)


def identity(family: str = "wafer_saw", machine_id: str | None = None) -> MachineIdentity:
    station = STATIONS[family]
    return MachineIdentity(
        machine_id or f"TEST-{station.station_id}",
        family,
        station.station_id,
        station.name,
    )


def window(
    channel: str,
    unit: str,
    values: list[float] | np.ndarray,
    *,
    start: float = 0.0,
    period: float = 1.0,
) -> ChannelWindow:
    array = np.asarray(values, dtype=np.float64)
    return ChannelWindow(
        channel,
        unit,
        start + np.arange(len(array), dtype=np.float64) * period,
        array,
    )


def feature_set(
    machine: MachineIdentity | None = None,
    *,
    value: float = 10.0,
    start: dt.datetime = NOW,
    end: dt.datetime | None = None,
) -> FeatureSet:
    owner = machine or identity()
    finish = end or start + dt.timedelta(seconds=60)
    return FeatureSet(
        owner,
        finish,
        EquipmentState.PROCESSING,
        start,
        finish,
        (
            Feature("spindle_current.median", value, "spindle", "location"),
            Feature("spindle_speed.median", value * 1000.0, "spindle", "location"),
        ),
    )


def family_dataset(origin: DataOrigin = DataOrigin.REAL_OSAT) -> FamilyDataset:
    samples: list[FamilySample] = []
    events: list[ObservedEvent] = []
    for machine_index in range(3):
        machine_id = f"WS-{machine_index + 1:02d}"
        event_id = f"bearing-{machine_index}"
        events.append(ObservedEvent(event_id, machine_id, NOW + dt.timedelta(days=2)))
        for row in range(4):
            positive = row >= 2
            samples.append(
                FamilySample(
                    f"{machine_id}-{row}",
                    machine_id,
                    NOW + dt.timedelta(hours=row),
                    {"current": float(row + machine_index), "vibration": float(positive * 4 + row)},
                    event_id if positive else None,
                )
            )
    return FamilyDataset(
        "wafer_saw",
        origin,
        tuple(samples),
        tuple(events),
        NOW,
        NOW + dt.timedelta(days=3),
    )


def good_status() -> TelemetryStatus:
    return TelemetryStatus(True, True, frozenset({"spindle_current", "spindle_speed"}), ())


def model_result(score: float, subsystem: str = "spindle") -> MachineModelResult:
    z_score = 1.0 - 2.5 * np.log(max(1.0 - score, 1e-9))
    return MachineModelResult(
        True,
        (
            FeatureDeviation(
                "spindle_current.median",
                subsystem,
                "location",
                10.0,
                5.0,
                float(z_score),
                score,
            ),
            FeatureDeviation(
                "coolant_pressure.median",
                "cooling",
                "location",
                1.0,
                1.0,
                0.0,
                0.0,
            ),
        ),
    )
