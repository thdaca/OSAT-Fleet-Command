"""Step 08: asynchronous telemetry, status, and approved SECS/GEM mapping."""

from __future__ import annotations

import datetime as dt
from collections import deque
from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

import numpy as np

from ..common import (
    ChannelWindow,
    MachineIdentity,
    OperatingContext,
    RuntimeMode,
    TelemetrySample,
    utc,
)
from ..machines import StationDefinition


FEATURE_WINDOW = dt.timedelta(seconds=60)
MAXIMUM_CONTEXT_AGE = dt.timedelta(seconds=30)


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

    def poll(self) -> TelemetryBatch:
        ...


class QueuedTelemetrySource:
    runtime_mode = RuntimeMode.LIVE_EQUIPMENT

    def __init__(self, identity: MachineIdentity, profile: StationDefinition) -> None:
        if identity.family != profile.family or identity.station_id != profile.station_id:
            raise ValueError("Live source identity and station profile must match")
        self.identity = identity
        self.profile = profile
        self._batches: deque[TelemetryBatch] = deque()

    def submit(
        self,
        samples: Sequence[TelemetrySample],
        *,
        context: OperatingContext | None = None,
    ) -> None:
        self._batches.append(TelemetryBatch(tuple(samples), context))

    def poll(self) -> TelemetryBatch:
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
    ) -> None:
        if (
            identity.family != profile.family
            or identity.station_id != profile.station_id
            or not batches
        ):
            raise ValueError("Replay requires matching identity/profile and telemetry")
        self.identity = identity
        self.profile = profile
        self._batches = tuple(batches)
        self._position = 0

    def poll(self) -> TelemetryBatch:
        if self._position >= len(self._batches):
            raise TelemetrySourceExhausted("Historical replay is complete")
        batch = self._batches[self._position]
        self._position += 1
        return batch


class BoundedTelemetryStore:
    """Independent bounded streams; no synchronized sensor row exists."""

    def __init__(
        self,
        identity: MachineIdentity,
        profile: StationDefinition,
        *,
        maximum_samples_per_channel: int = 10_000,
        maximum_context_records: int = 2_000,
    ) -> None:
        if identity.family != profile.family or identity.station_id != profile.station_id:
            raise ValueError("Telemetry store identity and station profile must match")
        self.identity = identity
        self.profile = profile
        self._specs = {channel.name: channel for channel in profile.channels}
        self._timestamps = {
            channel.name: deque(maxlen=maximum_samples_per_channel)
            for channel in profile.channels
        }
        self._values = {
            channel.name: deque(maxlen=maximum_samples_per_channel)
            for channel in profile.channels
        }
        self._latest: dict[str, TelemetrySample] = {}
        self._contexts: deque[OperatingContext] = deque(maxlen=maximum_context_records)

    def append(self, sample: TelemetrySample) -> None:
        if sample.machine_id != self.identity.machine_id:
            raise TelemetryError("Telemetry sample belongs to another machine")
        spec = self._specs.get(sample.channel)
        if spec is None:
            raise TelemetryError(f"Unknown canonical channel {sample.channel!r}")
        if sample.unit != spec.unit:
            raise TelemetryError(
                f"{sample.channel} unit {sample.unit!r} does not match {spec.unit!r}"
            )
        if sample.source_id != spec.source_id:
            raise TelemetrySecurityError(
                f"Source {sample.source_id!r} is not approved for {sample.channel}"
            )
        epoch = sample.timestamp.timestamp()
        timestamps = self._timestamps[sample.channel]
        if timestamps and epoch <= timestamps[-1]:
            raise TelemetryError("Per-channel timestamps must be strictly increasing")
        timestamps.append(epoch)
        self._values[sample.channel].append(sample.value)
        self._latest[sample.channel] = sample

    def append_batch(self, batch: TelemetryBatch) -> None:
        for sample in batch.samples:
            self.append(sample)
        if batch.context is not None:
            self.append_context(batch.context)

    def append_context(self, context: OperatingContext) -> None:
        if context.machine_id != self.identity.machine_id:
            raise TelemetryError("Operating context belongs to another machine")
        if self._contexts and context.timestamp <= self._contexts[-1].timestamp:
            raise TelemetryError("Operating-context timestamps must increase")
        self._contexts.append(context)

    def latest(self, channel: str) -> TelemetrySample | None:
        return self._latest.get(channel)

    def latest_context(self, at: dt.datetime | None = None) -> OperatingContext | None:
        if not self._contexts:
            return None
        if at is None:
            return self._contexts[-1]
        end = utc(at)
        return next(
            (context for context in reversed(self._contexts) if context.timestamp <= end),
            None,
        )

    def window(
        self,
        channel: str,
        *,
        end: dt.datetime,
        duration: dt.timedelta = FEATURE_WINDOW,
    ) -> ChannelWindow | None:
        if duration <= dt.timedelta(0):
            raise ValueError("Telemetry window duration must be positive")
        timestamps = self._timestamps.get(channel)
        if not timestamps:
            return None
        end_epoch = utc(end).timestamp()
        start_epoch = end_epoch - duration.total_seconds()
        selected_t: list[float] = []
        selected_v: list[float] = []
        values = self._values[channel]
        for index in range(len(timestamps) - 1, -1, -1):
            stamp = timestamps[index]
            if stamp > end_epoch:
                continue
            if stamp < start_epoch:
                break
            selected_t.append(stamp)
            selected_v.append(values[index])
        if not selected_t:
            return None
        return ChannelWindow(
            channel=channel,
            unit=self._specs[channel].unit,
            timestamps=np.asarray(selected_t[::-1], dtype=np.float64),
            values=np.asarray(selected_v[::-1], dtype=np.float64),
        )

    def windows(
        self,
        channels: Sequence[str],
        *,
        end: dt.datetime,
        duration: dt.timedelta = FEATURE_WINDOW,
    ) -> dict[str, ChannelWindow]:
        result: dict[str, ChannelWindow] = {}
        for channel in channels:
            window = self.window(channel, end=end, duration=duration)
            if window is not None:
                result[channel] = window
        return result


@dataclass(frozen=True)
class TelemetryStatus:
    valid: bool
    observable: bool
    usable_channels: frozenset[str]
    issues: tuple[str, ...]


def assess_telemetry(
    store: BoundedTelemetryStore,
    *,
    now: dt.datetime,
    windows: Mapping[str, ChannelWindow] | None = None,
) -> TelemetryStatus:
    """Assess validity and observability together without collapsing them."""

    current = utc(now)
    issues: list[str] = []
    usable: set[str] = set()
    required_failure = False
    available_windows = windows or store.windows(
        [channel.name for channel in store.profile.channels], end=current
    )
    for spec in store.profile.channels:
        latest = store.latest(spec.name)
        window = available_windows.get(spec.name)
        problem: str | None = None
        if latest is None:
            problem = "missing"
        elif (current - latest.timestamp).total_seconds() > spec.stale_seconds:
            problem = "stale"
        elif window is None or len(window.values) < 3:
            problem = "insufficient history"
        elif not bool(np.isfinite(window.values).all()):
            problem = "non-finite"
        if problem is None:
            usable.add(spec.name)
        else:
            issues.append(f"{spec.name}: {problem}")
            required_failure = required_failure or spec.required
    context = store.latest_context(current)
    context_observable = context is not None
    if context is None:
        issues.append("operating context: missing")
    elif current - context.timestamp > MAXIMUM_CONTEXT_AGE:
        context_observable = False
        issues.append("operating context: stale")
    return TelemetryStatus(
        valid=not required_failure,
        observable=not required_failure and context_observable,
        usable_channels=frozenset(usable),
        issues=tuple(issues),
    )


_PROCESS_IP_TOKENS = (
    "recipe",
    "ppid",
    "wafer_map",
    "wafermap",
    "geometry",
    "process_window",
    "equipment_constant",
    "calibration_constant",
)


def _reject_process_ip(value: Any, path: str = "root") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(token in normalized for token in _PROCESS_IP_TOKENS):
                raise TelemetrySecurityError(f"Prohibited process field at {path}.{key}")
            _reject_process_ip(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _reject_process_ip(child, f"{path}[{index}]")
    elif isinstance(value, str):
        normalized = value.lower().replace("-", "_")
        if any(token in normalized for token in _PROCESS_IP_TOKENS):
            raise TelemetrySecurityError(f"Prohibited process identifier at {path}")


class SecsGemAdapter:
    """Map approved S6F11 source IDs to independent canonical samples."""

    def __init__(
        self,
        identity: MachineIdentity,
        profile: StationDefinition,
        approved_mapping: Mapping[str, str] | None = None,
    ) -> None:
        if identity.family != profile.family or identity.station_id != profile.station_id:
            raise ValueError("SECS/GEM identity and station profile must match")
        self.identity = identity
        self.profile = profile
        known = {channel.name: channel for channel in profile.channels}
        mapping = {channel.source_id: channel.name for channel in profile.channels}
        for source_id, canonical in (approved_mapping or {}).items():
            if canonical not in known:
                raise ValueError(f"Mapping target {canonical!r} is not approved")
            mapping[str(source_id)] = canonical
        self._mapping = mapping
        self._specs = known

    def parse(self, payload: Mapping[str, Any], *, received_at: dt.datetime) -> tuple[TelemetrySample, ...]:
        _reject_process_ip(payload)
        if int(payload.get("stream", 6)) != 6 or int(payload.get("function", 11)) != 11:
            raise ValueError("Only SECS/GEM S6F11 reports are accepted")
        variables = payload.get("variables", ())
        if not isinstance(variables, (list, tuple)):
            raise ValueError("S6F11 variables must be a list")
        timestamp = utc(received_at)
        samples: list[TelemetrySample] = []
        unknown: list[str] = []
        for item in variables:
            if not isinstance(item, Mapping) or "id" not in item or "value" not in item:
                raise ValueError("Each status variable requires id and value")
            source_id = str(item["id"])
            canonical = self._mapping.get(source_id)
            if canonical is None:
                unknown.append(source_id)
                continue
            spec = self._specs[canonical]
            samples.append(
                TelemetrySample(
                    machine_id=self.identity.machine_id,
                    channel=canonical,
                    timestamp=timestamp,
                    value=float(item["value"]),
                    unit=spec.unit,
                    source_id=spec.source_id,
                )
            )
        if unknown:
            raise TelemetrySecurityError(
                "Unknown source identifiers rejected: " + ", ".join(sorted(unknown))
            )
        return tuple(samples)
