"""Step 08 input streams: live queue, replay and their shared batch contract."""
from __future__ import annotations

import datetime as dt
from ...pre_steps.pre01_common.contracts import (
    DataOrigin,
    MachineIdentity,
    OperatingContext,
    RuntimeMode,
    TelemetrySample,
)
from ...pre_steps.pre02_machine_registry.registry import StationDefinition

from collections import deque
from dataclasses import dataclass
from threading import Lock
from typing import Protocol

MAXIMUM_LIVE_FUTURE_SKEW = dt.timedelta(seconds=5)
MAXIMUM_LIVE_SAMPLES_PER_BATCH = 256

class TelemetryError(ValueError):
    pass


class TelemetrySecurityError(RuntimeError):
    pass


class NoNewTelemetry(RuntimeError):
    pass


class TelemetrySourceExhausted(RuntimeError):
    pass


@dataclass(frozen=True)
class TelemetryBatch:
    samples: tuple[TelemetrySample, ...]
    context: OperatingContext | None = None


class TelemetrySource(Protocol):
    identity: MachineIdentity
    profile: StationDefinition
    runtime_mode: RuntimeMode
    origin: DataOrigin

    def poll(self) -> TelemetryBatch:
        ...


class QueuedTelemetrySource:
    runtime_mode = RuntimeMode.LIVE_EQUIPMENT
    origin = DataOrigin.REAL_OSAT

    def __init__(
        self,
        identity: MachineIdentity,
        profile: StationDefinition,
        *,
        maximum_queued_batches: int = 256,
    ) -> None:
        if identity.family != profile.family or identity.station_id != profile.station_id:
            raise ValueError("Live source identity and station profile must match")
        if maximum_queued_batches < 1:
            raise ValueError("Maximum queued batches must be positive")
        self.identity = identity
        self.profile = profile
        self._batches: deque[TelemetryBatch] = deque()
        self._maximum_queued_batches = maximum_queued_batches
        self._lock = Lock()

    def submit(
        self,
        samples: Sequence[TelemetrySample],
        *,
        context: OperatingContext | None = None,
    ) -> None:
        if len(samples) > MAXIMUM_LIVE_SAMPLES_PER_BATCH:
            raise TelemetryError(
                "Live telemetry batches may contain at most "
                f"{MAXIMUM_LIVE_SAMPLES_PER_BATCH} samples"
            )
        batch = TelemetryBatch(tuple(samples), context)
        if not batch.samples and batch.context is None:
            raise TelemetryError("Live telemetry batches must contain samples or context")
        latest_allowed = dt.datetime.now(dt.timezone.utc) + MAXIMUM_LIVE_FUTURE_SKEW
        if any(sample.timestamp > latest_allowed for sample in batch.samples):
            raise TelemetryError("Live telemetry timestamp exceeds the future-clock tolerance")
        if batch.context is not None and batch.context.timestamp > latest_allowed:
            raise TelemetryError(
                "Live operating-context timestamp exceeds the future-clock tolerance"
            )
        with self._lock:
            if len(self._batches) >= self._maximum_queued_batches:
                raise TelemetryError("Live telemetry input queue is full")
            self._batches.append(batch)

    def poll(self) -> TelemetryBatch:
        with self._lock:
            if not self._batches:
                raise NoNewTelemetry("No new live telemetry is queued")
            return self._batches.popleft()


class ReplayTelemetrySource:
    runtime_mode = RuntimeMode.REAL_REPLAY

    def __init__(
        self,
        identity: MachineIdentity,
        profile: StationDefinition,
        batches: Sequence[TelemetryBatch],
        *,
        origin: DataOrigin,
    ) -> None:
        replay_batches = tuple(batches)
        if identity.family != profile.family or identity.station_id != profile.station_id:
            raise ValueError("Replay requires matching identity/profile and telemetry")
        if not replay_batches:
            raise ValueError("Replay requires matching identity/profile and telemetry")
        if any(not batch.samples and batch.context is None for batch in replay_batches):
            raise ValueError("Replay telemetry batches must not be empty")
        self.identity = identity
        self.profile = profile
        self.origin = origin
        self._batches = replay_batches
        self._position = 0

    def poll(self) -> TelemetryBatch:
        if self._position >= len(self._batches):
            raise TelemetrySourceExhausted("Historical replay is complete")
        batch = self._batches[self._position]
        self._position += 1
        return batch


