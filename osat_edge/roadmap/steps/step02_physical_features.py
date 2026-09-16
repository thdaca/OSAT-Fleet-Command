"""Step 02: defensible low-rate physical/statistical features."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Mapping

import numpy as np

from ..pre_steps.pre01_common import ChannelWindow, EquipmentState, MachineIdentity, utc
from ..pre_steps.pre02_machine_registry import StationDefinition


@dataclass(frozen=True)
class Feature:
    name: str
    value: float
    subsystem: str
    kind: str
    relation_id: str | None = None

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.name, self.subsystem, self.kind)):
            raise ValueError("Feature name, subsystem, and kind are required")
        if self.relation_id is not None and not self.relation_id.strip():
            raise ValueError("Feature relation ID must be nonempty when provided")
        if not np.isfinite(self.value):
            raise ValueError("Feature value must be finite")


@dataclass(frozen=True)
class FeatureSet:
    machine: MachineIdentity
    timestamp: dt.datetime
    equipment_state: EquipmentState
    window_start: dt.datetime
    window_end: dt.datetime
    features: tuple[Feature, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestamp", utc(self.timestamp))
        object.__setattr__(self, "window_start", utc(self.window_start))
        object.__setattr__(self, "window_end", utc(self.window_end))
        if self.window_end < self.window_start:
            raise ValueError("Feature window end precedes its start")
        names = [feature.name for feature in self.features]
        if len(names) != len(set(names)):
            raise ValueError("Feature names must be unique")

    @property
    def by_name(self) -> dict[str, Feature]:
        return {feature.name: feature for feature in self.features}


def robust_slope(window: ChannelWindow) -> float:
    if len(window.values) < 2 or window.duration_seconds <= 0:
        return 0.0
    middle = len(window.values) // 2
    change = np.median(window.values[middle:]) - np.median(window.values[:middle])
    elapsed = np.median(window.timestamps[middle:]) - np.median(window.timestamps[:middle])
    if elapsed <= 0:
        return 0.0
    return float(change / elapsed)


def extract_physical_features(
    machine: MachineIdentity,
    station: StationDefinition,
    windows: Mapping[str, ChannelWindow],
    *,
    timestamp: dt.datetime,
    equipment_state: EquipmentState,
    window_start: dt.datetime,
    minimum_coverage: float = 0.5,
) -> FeatureSet:
    """Return median, MAD, and robust slope for usable asynchronous windows."""

    end = utc(timestamp)
    start = utc(window_start)
    duration = max((end - start).total_seconds(), 0.0)
    features: list[Feature] = []
    for channel in station.channels:
        window = windows.get(channel.name)
        if window is None or len(window.values) < 3:
            continue
        expected = max(duration / channel.period_seconds, 1.0)
        if len(window.values) / expected < minimum_coverage:
            continue
        median = float(np.median(window.values))
        mad = float(np.median(np.abs(window.values - median)))
        values = (
            ("median", median, "location"),
            ("mad", mad, "spread"),
            ("robust_slope_per_second", robust_slope(window), "trend"),
        )
        for suffix, value, kind in values:
            features.append(
                Feature(
                    name=f"{channel.name}.{suffix}",
                    value=value,
                    subsystem=channel.subsystem,
                    kind=kind,
                )
            )
    return FeatureSet(
        machine=machine,
        timestamp=end,
        equipment_state=equipment_state,
        window_start=start,
        window_end=end,
        features=tuple(features),
    )
