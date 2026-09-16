"""Step 06: confirmed-healthy history for one exact installed machine."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from ..common import DataOrigin, EquipmentState, MachineIdentity, utc
from .step02_physical_features import FeatureSet


@dataclass(frozen=True)
class HealthyInterval:
    machine_id: str
    start: dt.datetime
    end: dt.datetime
    equipment_states: tuple[EquipmentState, ...] = (EquipmentState.PROCESSING,)

    def __post_init__(self) -> None:
        object.__setattr__(self, "start", utc(self.start))
        object.__setattr__(self, "end", utc(self.end))
        if self.end <= self.start or not self.equipment_states:
            raise ValueError("Healthy interval must have duration and operating states")

    def contains(self, feature_set: FeatureSet) -> bool:
        return (
            feature_set.machine.machine_id == self.machine_id
            and self.start <= feature_set.window_start
            and feature_set.window_end <= self.end
            and feature_set.equipment_state in self.equipment_states
        )


@dataclass(frozen=True)
class MachineHistory:
    machine: MachineIdentity
    origin: DataOrigin
    feature_sets: tuple[FeatureSet, ...]
    confirmed_healthy: tuple[HealthyInterval, ...]

    def __post_init__(self) -> None:
        if any(feature_set.machine != self.machine for feature_set in self.feature_sets):
            raise ValueError("Machine history cannot mix exact-machine identities")
        if any(interval.machine_id != self.machine.machine_id for interval in self.confirmed_healthy):
            raise ValueError("Healthy intervals belong to another machine")
        if not self.confirmed_healthy:
            raise ValueError("Confirmed healthy intervals are required")

    def healthy_feature_sets(self) -> tuple[FeatureSet, ...]:
        return tuple(
            feature_set
            for feature_set in self.feature_sets
            if any(interval.contains(feature_set) for interval in self.confirmed_healthy)
        )
