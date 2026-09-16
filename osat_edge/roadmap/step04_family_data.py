"""Step 04: strict real same-family equipment data."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

import numpy as np

from ..common import DataOrigin, utc


@dataclass(frozen=True)
class ObservedEvent:
    event_id: str
    machine_id: str
    timestamp: dt.datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestamp", utc(self.timestamp))
        if not self.event_id.strip() or not self.machine_id.strip():
            raise ValueError("Observed event ID and machine ID are required")


@dataclass(frozen=True)
class FamilySample:
    sample_id: str
    machine_id: str
    timestamp: dt.datetime
    features: Mapping[str, float]
    future_event_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestamp", utc(self.timestamp))
        if not self.sample_id.strip() or not self.machine_id.strip():
            raise ValueError("Family sample ID and machine ID are required")
        if self.future_event_id is not None and not self.future_event_id.strip():
            raise ValueError("A supplied future event ID must be nonempty")
        values = {str(name): float(value) for name, value in self.features.items()}
        if (
            not values
            or not all(name.strip() for name in values)
            or not all(np.isfinite(value) for value in values.values())
        ):
            raise ValueError("Family sample features must be present and finite")
        object.__setattr__(self, "features", MappingProxyType(values))


@dataclass(frozen=True)
class FamilyDataset:
    family: str
    origin: DataOrigin
    samples: tuple[FamilySample, ...]
    events: tuple[ObservedEvent, ...]
    collected_start: dt.datetime
    collected_end: dt.datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "collected_start", utc(self.collected_start))
        object.__setattr__(self, "collected_end", utc(self.collected_end))
        if self.collected_end < self.collected_start:
            raise ValueError("Family collection end precedes start")
        if not self.family.strip() or not self.samples:
            raise ValueError("Family and samples are required")
        if any(
            not self.collected_start <= item.timestamp <= self.collected_end
            for item in (*self.samples, *self.events)
        ):
            raise ValueError("Family samples and events must lie inside the collection period")
        if len({sample.sample_id for sample in self.samples}) != len(self.samples):
            raise ValueError("Family sample IDs must be globally unique")
        schema = set(self.samples[0].features)
        if any(set(sample.features) != schema for sample in self.samples[1:]):
            raise ValueError("Every family sample must use the same feature schema")
        event_keys = [(event.machine_id, event.event_id) for event in self.events]
        if len(event_keys) != len(set(event_keys)):
            raise ValueError("Observed event machine/event keys must be unique")
        events = {
            (event.machine_id, event.event_id): event
            for event in self.events
        }
        for sample in self.samples:
            if sample.future_event_id is not None:
                event = events.get((sample.machine_id, sample.future_event_id))
                if event is None:
                    raise ValueError("Positive family windows must reference an observed event")
                if event.timestamp <= sample.timestamp:
                    raise ValueError("Referenced equipment event must occur after its training sample")

    @property
    def machine_ids(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(sample.machine_id for sample in self.samples))

    @property
    def feature_names(self) -> tuple[str, ...]:
        return tuple(self.samples[0].features)

    @property
    def independent_event_count(self) -> int:
        return len(
            {
                (sample.machine_id, sample.future_event_id)
                for sample in self.samples
                if sample.future_event_id is not None
            }
        )

    def training_arrays(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        matrix = np.asarray(
            [[sample.features[name] for name in self.feature_names] for sample in self.samples],
            dtype=np.float64,
        )
        labels = np.asarray(
            [int(sample.future_event_id is not None) for sample in self.samples],
            dtype=np.int8,
        )
        machines = np.asarray([sample.machine_id for sample in self.samples], dtype=str)
        return matrix, labels, machines
