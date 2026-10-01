"""Step 08 fail-closed S6F11 mapping; this adapter cannot control equipment."""
from __future__ import annotations

import datetime as dt
from ...pre_steps.pre01_common.contracts import MachineIdentity, TelemetrySample, utc
from ...pre_steps.pre02_machine_registry.registry import StationDefinition

from typing import Any, Mapping
from .sources import TelemetrySecurityError

MAXIMUM_SECS_VARIABLES = 256

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
            source_id = str(source_id)
            if not source_id.strip():
                raise ValueError("Custom source IDs must be nonempty")
            if canonical not in known:
                raise ValueError(f"Mapping target {canonical!r} is not approved")
            existing = mapping.get(source_id)
            if existing is not None and existing != canonical:
                raise TelemetrySecurityError(
                    f"Source {source_id!r} is already approved for {existing!r}"
                )
            mapping[source_id] = canonical
        self._mapping = mapping
        self._specs = known

    def parse(self, payload: Mapping[str, Any], *, received_at: dt.datetime) -> tuple[TelemetrySample, ...]:
        if not isinstance(payload, Mapping):
            raise ValueError("S6F11 payload must be an object")
        if set(payload) != {"stream", "function", "variables"}:
            raise ValueError(
                "S6F11 payload keys must be exactly stream, function, and variables"
            )
        if type(payload["stream"]) is not int or type(payload["function"]) is not int:
            raise ValueError("SECS/GEM stream and function must be exact integers")
        if payload["stream"] != 6 or payload["function"] != 11:
            raise ValueError("Only SECS/GEM S6F11 reports are accepted")
        variables = payload["variables"]
        if not isinstance(variables, list):
            raise ValueError("S6F11 variables must be a JSON list")
        if not variables or len(variables) > MAXIMUM_SECS_VARIABLES:
            raise ValueError(
                f"S6F11 variables must contain 1 to {MAXIMUM_SECS_VARIABLES} entries"
            )
        validated_variables: list[tuple[str, int | float]] = []
        for item in variables:
            if not isinstance(item, Mapping) or set(item) != {"id", "value"}:
                raise ValueError("Each status variable must contain exactly id and value")
            if not isinstance(item["id"], str) or not item["id"].strip():
                raise ValueError("Each status variable ID must be a nonempty string")
            if isinstance(item["value"], bool) or not isinstance(
                item["value"], (int, float)
            ):
                raise ValueError("Each status variable value must be numeric")
            validated_variables.append((item["id"], item["value"]))

        # Defense-in-depth inspection runs only after the input shape is known
        # to be flat and bounded, so recursive attacker-controlled structures
        # cannot reach the scanner.
        _reject_process_ip(payload)

        timestamp = utc(received_at)
        samples: list[TelemetrySample] = []
        unknown: list[str] = []
        resolved_channels: set[str] = set()
        for source_id, raw_value in validated_variables:
            canonical = self._mapping.get(source_id)
            if canonical is None:
                unknown.append(source_id)
                continue
            if canonical in resolved_channels:
                raise TelemetrySecurityError(
                    f"Multiple report variables resolve to canonical channel {canonical!r}"
                )
            resolved_channels.add(canonical)
            spec = self._specs[canonical]
            samples.append(
                TelemetrySample(
                    machine_id=self.identity.machine_id,
                    channel=canonical,
                    timestamp=timestamp,
                    value=float(raw_value),
                    unit=spec.unit,
                    source_id=spec.source_id,
                )
            )
        if unknown:
            raise TelemetrySecurityError(
                "Unknown source identifiers rejected: " + ", ".join(sorted(unknown))
            )
        return tuple(samples)
