"""Small contracts shared by multiple roadmap stages."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from enum import Enum

import numpy as np


VERSION = "0.2.6"
# POST04 reproduces frozen 0.2.5 experiments, not new 0.2.6 measurements.
FROZEN_EXTERNAL_EVIDENCE_VERSION = "0.2.5"
RELEASE_CLASS = "RESEARCH / DEVELOPMENT"


class DataOrigin(str, Enum):
    SYNTHETIC = "SYNTHETIC"
    EXTERNAL_BENCHMARK = "EXTERNAL_BENCHMARK"
    REAL_OSAT = "REAL_OSAT"


class RuntimeMode(str, Enum):
    SIMULATION = "SIMULATION"
    REAL_REPLAY = "REAL_REPLAY"
    LIVE_EQUIPMENT = "LIVE_EQUIPMENT"


class EquipmentState(str, Enum):
    UNKNOWN = "UNKNOWN"
    OFF = "OFF"
    IDLE = "IDLE"
    SETUP = "SETUP"
    PROCESSING = "PROCESSING"
    MAINTENANCE = "MAINTENANCE"
    FAULTED = "FAULTED"


class HealthState(str, Enum):
    UNKNOWN = "UNKNOWN"
    NORMAL = "NORMAL"
    WATCH = "WATCH"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"


def utc(value: dt.datetime, name: str = "timestamp") -> dt.datetime:
    """Return a timezone-aware timestamp normalized to UTC."""

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(dt.timezone.utc)


def health_rank(state: HealthState) -> int:
    return {
        HealthState.UNKNOWN: -1,
        HealthState.NORMAL: 0,
        HealthState.WATCH: 1,
        HealthState.DEGRADED: 2,
        HealthState.CRITICAL: 3,
    }[state]


@dataclass(frozen=True)
class MachineIdentity:
    machine_id: str
    family: str
    station_id: str
    name: str

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.machine_id, self.family, self.station_id)):
            raise ValueError("Machine ID, family, and station ID are required")


@dataclass(frozen=True)
class ChannelSpec:
    name: str
    unit: str
    subsystem: str
    required: bool
    period_seconds: float
    stale_seconds: float
    source_id: str

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.name, self.unit, self.subsystem, self.source_id)):
            raise ValueError("Channel name, unit, subsystem, and source ID are required")
        if (
            not np.isfinite(self.period_seconds)
            or not np.isfinite(self.stale_seconds)
            or self.period_seconds <= 0
            or self.stale_seconds < self.period_seconds
        ):
            raise ValueError("Channel timing must be positive and ordered")


@dataclass(frozen=True)
class TelemetrySample:
    machine_id: str
    channel: str
    timestamp: dt.datetime
    value: float
    unit: str
    source_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestamp", utc(self.timestamp))
        if not np.isfinite(self.value):
            raise ValueError("Telemetry value must be finite")


@dataclass(frozen=True)
class OperatingContext:
    machine_id: str
    timestamp: dt.datetime
    equipment_state: EquipmentState

    def __post_init__(self) -> None:
        if not isinstance(self.machine_id, str) or not self.machine_id.strip():
            raise ValueError("Operating-context machine ID is required")
        if not isinstance(self.equipment_state, EquipmentState):
            raise ValueError("Operating context requires an EquipmentState")
        object.__setattr__(self, "timestamp", utc(self.timestamp))


@dataclass(frozen=True)
class ChannelWindow:
    channel: str
    unit: str
    timestamps: np.ndarray
    values: np.ndarray

    def __post_init__(self) -> None:
        if not self.channel.strip() or not self.unit.strip():
            raise ValueError("Window channel and unit are required")
        timestamps = np.asarray(self.timestamps, dtype=np.float64).copy()
        values = np.asarray(self.values, dtype=np.float64).copy()
        if timestamps.ndim != 1 or values.ndim != 1:
            raise ValueError("Channel windows must be one-dimensional")
        if timestamps.shape != values.shape:
            raise ValueError("Window timestamps and values must align")
        if not bool(np.isfinite(timestamps).all()) or not bool(np.isfinite(values).all()):
            raise ValueError("Channel window values and timestamps must be finite")
        if len(timestamps) > 1 and not bool(np.all(np.diff(timestamps) > 0)):
            raise ValueError("Channel window timestamps must be strictly increasing")
        timestamps.setflags(write=False)
        values.setflags(write=False)
        object.__setattr__(self, "timestamps", timestamps)
        object.__setattr__(self, "values", values)

    @property
    def duration_seconds(self) -> float:
        if len(self.timestamps) < 2:
            return 0.0
        return float(self.timestamps[-1] - self.timestamps[0])
