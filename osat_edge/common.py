"""Small contracts shared by multiple roadmap stages."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from enum import Enum

import numpy as np


VERSION = "0.2.2"
RELEASE_CLASS = "RESEARCH / DEVELOPMENT"


class DataOrigin(str, Enum):
    SYNTHETIC = "SYNTHETIC"
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
        if self.period_seconds <= 0 or self.stale_seconds < self.period_seconds:
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
        object.__setattr__(self, "timestamp", utc(self.timestamp))


@dataclass(frozen=True)
class ChannelWindow:
    channel: str
    unit: str
    timestamps: np.ndarray
    values: np.ndarray

    def __post_init__(self) -> None:
        if self.timestamps.shape != self.values.shape:
            raise ValueError("Window timestamps and values must align")
        if self.timestamps.ndim != 1:
            raise ValueError("Channel windows must be one-dimensional")

    @property
    def duration_seconds(self) -> float:
        if len(self.timestamps) < 2:
            return 0.0
        return float(self.timestamps[-1] - self.timestamps[0])
