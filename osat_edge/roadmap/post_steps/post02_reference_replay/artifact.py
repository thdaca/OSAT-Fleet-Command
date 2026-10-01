"""POST02 strict checksum, schema and timeline validation of the reference artifact."""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from ...pre_steps.pre01_common.contracts import (
    DataOrigin,
    EquipmentState,
    HealthState,
    MachineIdentity,
    OperatingContext,
    RuntimeMode,
    TelemetrySample,
)
from ...pre_steps.pre02_machine_registry.registry import STATIONS, StationDefinition
from ...steps.step08_live_telemetry.sources import ReplayTelemetrySource, TelemetryBatch


REFERENCE_SCHEMA_VERSION = "1.0"
REFERENCE_RELEASE_VERSION = "0.2.3"
REFERENCE_DATASET_ID = "osat-reference-fleet-001"
REFERENCE_FILES = (
    "telemetry.csv",
    "context.csv",
    "source_mapping.json",
    "expected_checkpoints.json",
)
REFERENCE_DIRECTORY_FILES = frozenset(
    (*REFERENCE_FILES, "manifest.json", "README.md", "generate_reference_replay.py")
)
DEFAULT_REFERENCE_DIRECTORY = (
    Path(__file__).resolve().parent
    / "resources"
)
_DATASET_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,79}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REQUIRED_CLAIMS = frozenset(
    {
        "SYNTHETIC REFERENCE REPLAY",
        "NOT REAL OSAT DATA",
        "NOT PLANT VALIDATION",
        "NOT PRODUCTION QUALIFICATION",
    }
)
_REQUIRED_CLASSIFICATION = frozenset(
    {"FROZEN", "EDUCATIONAL", "PIPELINE-REFERENCE DATA"}
)
_REFERENCE_PHASES = frozenset(
    {
        "healthy_stable",
        "healthy_variation",
        "optional_missing",
        "required_stale",
        "recovery",
        "physics_outside_calibration",
        "physics_in_domain",
        "positive_load_residual",
    }
)
_MANIFEST_FIELDS = frozenset(
    {
        "dataset_id",
        "schema_version",
        "release_version",
        "title",
        "origin",
        "runtime_mode",
        "classification",
        "production_qualified",
        "machine",
        "timeline",
        "phases",
        "files",
        "claims",
    }
)
_EXPECTED_OBSERVATION_FIELDS = frozenset(
    {
        "health",
        "telemetry_valid",
        "physics_residual_present",
        "ticket_created_this_tick",
        "active_ticket_count",
    }
)


class ReferenceReplayError(ValueError):
    """The frozen reference artifact failed a provenance or schema check."""


class _ValidatedReferenceReplaySource(ReplayTelemetrySource):
    """Marks the checksum-validated bundled replay as demo-ticket eligible."""

    demo_ticket_authorized = True


@dataclass(frozen=True)
class ReferenceReplayDataset:
    directory: Path
    manifest: Mapping[str, Any]
    identity: MachineIdentity
    station: StationDefinition
    source: ReplayTelemetrySource
    telemetry_rows: int
    context_rows: int
    expected_checkpoints: Mapping[str, Any]


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, child in pairs:
        if key in value:
            raise ReferenceReplayError(f"Duplicate JSON key {key!r}")
        value[key] = child
    return value


def _read_json(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReferenceReplayError(f"Cannot read valid JSON from {path.name}") from exc
    if not isinstance(value, Mapping):
        raise ReferenceReplayError(f"{path.name} must contain one JSON object")
    return value


def _utc_timestamp(raw: str, field: str) -> dt.datetime:
    if not raw.endswith("Z"):
        raise ReferenceReplayError(f"{field} must use an explicit UTC Z suffix")
    try:
        value = dt.datetime.fromisoformat(f"{raw[:-1]}+00:00")
    except ValueError as exc:
        raise ReferenceReplayError(f"{field} is not a valid ISO-8601 timestamp") from exc
    if value.utcoffset() != dt.timedelta(0):
        raise ReferenceReplayError(f"{field} must be UTC")
    return value.astimezone(dt.timezone.utc)


def _require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReferenceReplayError(f"{field} must be a nonempty string")
    return value


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        raise ReferenceReplayError(f"Cannot read {path.name}") from exc
    return digest.hexdigest()


def _exact_string_set(value: Any, field: str, required: frozenset[str]) -> None:
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) or not item.strip() for item in value)
        or len(value) != len(set(value))
        or set(value) != set(required)
    ):
        raise ReferenceReplayError(
            f"{field} must contain exactly: {', '.join(sorted(required))}"
        )


def _require_exact_keys(
    value: Mapping[str, Any], field: str, expected: frozenset[str]
) -> None:
    actual = set(value)
    unknown = sorted(actual - expected)
    missing = sorted(expected - actual)
    if unknown:
        raise ReferenceReplayError(
            f"{field} has unknown fields: {', '.join(str(name) for name in unknown)}"
        )
    if missing:
        raise ReferenceReplayError(
            f"{field} is missing fields: {', '.join(str(name) for name in missing)}"
        )


def _validate_manifest(directory: Path) -> Mapping[str, Any]:
    path = directory / "manifest.json"
    if not path.is_file():
        raise ReferenceReplayError("Reference replay manifest.json is missing")
    manifest = _read_json(path)
    _require_exact_keys(manifest, "manifest", _MANIFEST_FIELDS)
    dataset_id = _require_string(manifest.get("dataset_id"), "manifest.dataset_id")
    if not _DATASET_ID.fullmatch(dataset_id):
        raise ReferenceReplayError("manifest.dataset_id has an invalid format")
    if dataset_id != REFERENCE_DATASET_ID:
        raise ReferenceReplayError("Unsupported reference replay dataset_id")
    if manifest.get("schema_version") != REFERENCE_SCHEMA_VERSION:
        raise ReferenceReplayError("Unsupported reference replay schema_version")
    if manifest.get("release_version") != REFERENCE_RELEASE_VERSION:
        raise ReferenceReplayError("Reference replay release_version is not the frozen release")
    if manifest.get("origin") != DataOrigin.SYNTHETIC.value:
        raise ReferenceReplayError("Reference replay origin must be SYNTHETIC")
    if manifest.get("runtime_mode") != RuntimeMode.REAL_REPLAY.value:
        raise ReferenceReplayError("Reference replay runtime_mode must be REAL_REPLAY")
    if manifest.get("production_qualified") is not False:
        raise ReferenceReplayError("Reference replay production_qualified must be false")
    _exact_string_set(manifest.get("claims"), "manifest.claims", _REQUIRED_CLAIMS)
    _exact_string_set(
        manifest.get("classification"),
        "manifest.classification",
        _REQUIRED_CLASSIFICATION,
    )
    _require_string(manifest.get("title"), "manifest.title")
    files = manifest.get("files")
    if not isinstance(files, Mapping) or set(files) != set(REFERENCE_FILES):
        raise ReferenceReplayError("Manifest must checksum the four reference data files")
    for name in REFERENCE_FILES:
        expected = files.get(name)
        if not isinstance(expected, str) or not _SHA256.fullmatch(expected):
            raise ReferenceReplayError(f"Invalid SHA-256 for {name}")
        child = directory / name
        if not child.is_file():
            raise ReferenceReplayError(f"Reference replay file {name} is missing")
        if _file_sha256(child) != expected:
            raise ReferenceReplayError(f"Checksum mismatch for {name}")
    return manifest


def _load_identity(
    manifest: Mapping[str, Any],
) -> tuple[MachineIdentity, StationDefinition]:
    machine = manifest.get("machine")
    if not isinstance(machine, Mapping):
        raise ReferenceReplayError("manifest.machine must be an object")
    _require_exact_keys(
        machine,
        "manifest.machine",
        frozenset({"machine_id", "family", "station_id", "name"}),
    )
    family = _require_string(machine.get("family"), "manifest.machine.family")
    try:
        station = STATIONS[family]
    except KeyError as exc:
        raise ReferenceReplayError(f"Unsupported reference machine family {family!r}") from exc
    identity = MachineIdentity(
        machine_id=_require_string(machine.get("machine_id"), "manifest.machine.machine_id"),
        family=family,
        station_id=_require_string(machine.get("station_id"), "manifest.machine.station_id"),
        name=_require_string(machine.get("name"), "manifest.machine.name"),
    )
    if identity.station_id != station.station_id:
        raise ReferenceReplayError("Reference machine family/station identity mismatch")
    return identity, station


def _load_mapping(
    path: Path,
    *,
    dataset_id: str,
    identity: MachineIdentity,
    station: StationDefinition,
) -> dict[str, tuple[str, str, str]]:
    value = _read_json(path)
    _require_exact_keys(
        value,
        "source_mapping",
        frozenset({"dataset_id", "schema_version", "origin", "machine_id", "mappings"}),
    )
    if value.get("schema_version") != REFERENCE_SCHEMA_VERSION:
        raise ReferenceReplayError("Unsupported source-mapping schema_version")
    if value.get("dataset_id") != dataset_id:
        raise ReferenceReplayError("Source mapping belongs to another dataset")
    if value.get("origin") != DataOrigin.SYNTHETIC.value:
        raise ReferenceReplayError("Source mapping origin must be SYNTHETIC")
    if value.get("machine_id") != identity.machine_id:
        raise ReferenceReplayError("Source mapping belongs to another machine")
    rows = value.get("mappings")
    if not isinstance(rows, list) or not rows:
        raise ReferenceReplayError("Source mapping requires a nonempty mappings list")
    specs = {spec.name: spec for spec in station.channels}
    result: dict[str, tuple[str, str, str]] = {}
    canonical_seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ReferenceReplayError(f"Mapping row {index} must be an object")
        _require_exact_keys(
            row,
            f"mappings[{index}]",
            frozenset({"canonical_channel", "source_id", "unit"}),
        )
        source_id = _require_string(row.get("source_id"), f"mappings[{index}].source_id")
        canonical = _require_string(
            row.get("canonical_channel"), f"mappings[{index}].canonical_channel"
        )
        unit = _require_string(row.get("unit"), f"mappings[{index}].unit")
        spec = specs.get(canonical)
        if spec is None:
            raise ReferenceReplayError(f"Mapping target {canonical!r} is not approved")
        if unit != spec.unit:
            raise ReferenceReplayError(f"Mapping unit for {canonical} is not approved")
        if source_id in result or canonical in canonical_seen:
            raise ReferenceReplayError("Source mapping IDs and canonical channels must be unique")
        result[source_id] = (canonical, unit, spec.source_id)
        canonical_seen.add(canonical)
    if canonical_seen != set(specs):
        raise ReferenceReplayError("Source mapping must explicitly cover every station channel")
    return result


def _csv_rows(path: Path, expected_columns: list[str]) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != expected_columns:
                raise ReferenceReplayError(
                    f"{path.name} columns must be {','.join(expected_columns)}"
                )
            rows = []
            for row_number, row in enumerate(reader, start=2):
                if None in row:
                    raise ReferenceReplayError(
                        f"{path.name} row {row_number} has surplus fields"
                    )
                if any(row.get(column) is None for column in expected_columns):
                    raise ReferenceReplayError(
                        f"{path.name} row {row_number} has missing fields"
                    )
                rows.append({column: str(row[column]) for column in expected_columns})
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ReferenceReplayError(f"Cannot read valid CSV from {path.name}") from exc
    if not rows:
        raise ReferenceReplayError(f"{path.name} must contain at least one data row")
    return rows


def _load_telemetry(
    path: Path,
    *,
    identity: MachineIdentity,
    mapping: Mapping[str, tuple[str, str, str]],
) -> list[TelemetrySample]:
    rows = _csv_rows(
        path, ["timestamp_utc", "machine_id", "source_id", "value", "unit"]
    )
    samples: list[TelemetrySample] = []
    latest: dict[str, dt.datetime] = {}
    seen: set[tuple[str, dt.datetime]] = set()
    for index, row in enumerate(rows, start=2):
        if row["machine_id"] != identity.machine_id:
            raise ReferenceReplayError(f"telemetry.csv row {index} belongs to another machine")
        source_id = row["source_id"]
        mapped = mapping.get(source_id)
        if mapped is None:
            raise ReferenceReplayError(f"telemetry.csv row {index} has an unapproved source_id")
        canonical, approved_unit, approved_source_id = mapped
        if row["unit"] != approved_unit:
            raise ReferenceReplayError(f"telemetry.csv row {index} has an invalid unit")
        timestamp = _utc_timestamp(row["timestamp_utc"], f"telemetry.csv row {index}")
        key = (canonical, timestamp)
        if key in seen:
            raise ReferenceReplayError("Duplicate per-channel telemetry timestamp")
        if canonical in latest and timestamp <= latest[canonical]:
            raise ReferenceReplayError("Per-channel telemetry timestamps must increase")
        try:
            number = float(row["value"])
        except ValueError as exc:
            raise ReferenceReplayError(f"telemetry.csv row {index} value is not numeric") from exc
        if not math.isfinite(number):
            raise ReferenceReplayError(f"telemetry.csv row {index} value must be finite")
        samples.append(
            TelemetrySample(
                identity.machine_id,
                canonical,
                timestamp,
                number,
                approved_unit,
                approved_source_id,
            )
        )
        latest[canonical] = timestamp
        seen.add(key)
    return samples


def _load_context(path: Path, *, identity: MachineIdentity) -> list[OperatingContext]:
    rows = _csv_rows(path, ["timestamp_utc", "machine_id", "equipment_state"])
    contexts: list[OperatingContext] = []
    previous: dt.datetime | None = None
    for index, row in enumerate(rows, start=2):
        if row["machine_id"] != identity.machine_id:
            raise ReferenceReplayError(f"context.csv row {index} belongs to another machine")
        timestamp = _utc_timestamp(row["timestamp_utc"], f"context.csv row {index}")
        if previous is not None and timestamp <= previous:
            raise ReferenceReplayError("Operating-context timestamps must increase")
        try:
            state = EquipmentState(row["equipment_state"])
        except ValueError as exc:
            raise ReferenceReplayError(f"context.csv row {index} has an invalid state") from exc
        contexts.append(OperatingContext(identity.machine_id, timestamp, state))
        previous = timestamp
    return contexts


def _load_checkpoints(
    path: Path,
    *,
    dataset_id: str,
    station: StationDefinition,
    start: dt.datetime,
    end: dt.datetime,
) -> Mapping[str, Any]:
    value = _read_json(path)
    _require_exact_keys(
        value,
        "expected_checkpoints",
        frozenset(
            {
                "dataset_id",
                "schema_version",
                "note",
                "expected_final_state",
                "expected_subsystem",
                "expected_ticket_priority",
                "checkpoints",
            }
        ),
    )
    if value.get("schema_version") != REFERENCE_SCHEMA_VERSION:
        raise ReferenceReplayError("Unsupported expected-checkpoint schema_version")
    if value.get("dataset_id") != dataset_id:
        raise ReferenceReplayError("Expected checkpoints belong to another dataset")
    _require_string(value.get("note"), "expected_checkpoints.note")
    try:
        HealthState(value.get("expected_final_state"))
    except (TypeError, ValueError) as exc:
        raise ReferenceReplayError("expected_final_state must be a valid health state") from exc
    expected_subsystem = _require_string(
        value.get("expected_subsystem"), "expected_subsystem"
    )
    station_subsystems = {channel.subsystem for channel in station.channels}
    if expected_subsystem not in station_subsystems:
        raise ReferenceReplayError("expected_subsystem is not present in the station profile")
    if value.get("expected_ticket_priority") not in {"HIGH", "URGENT"}:
        raise ReferenceReplayError("expected_ticket_priority must be HIGH or URGENT")
    rows = value.get("checkpoints")
    if not isinstance(rows, list) or not rows:
        raise ReferenceReplayError("Expected checkpoints require a nonempty list")
    names: set[str] = set()
    previous: dt.datetime | None = None
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ReferenceReplayError(f"Checkpoint {index} must be an object")
        _require_exact_keys(
            row,
            f"checkpoints[{index}]",
            frozenset({"name", "timestamp_utc", "expected"}),
        )
        name = _require_string(row.get("name"), f"checkpoints[{index}].name")
        timestamp = _utc_timestamp(
            _require_string(row.get("timestamp_utc"), f"checkpoints[{index}].timestamp_utc"),
            f"checkpoints[{index}].timestamp_utc",
        )
        expected = row.get("expected")
        if not isinstance(expected, Mapping) or not expected:
            raise ReferenceReplayError(f"Checkpoint {name} requires expected observations")
        unknown_expected = sorted(set(expected) - _EXPECTED_OBSERVATION_FIELDS)
        if unknown_expected:
            raise ReferenceReplayError(
                f"Checkpoint {name} has unknown expected fields: "
                + ", ".join(str(field) for field in unknown_expected)
            )
        if "health" in expected:
            try:
                HealthState(expected["health"])
            except (TypeError, ValueError) as exc:
                raise ReferenceReplayError(
                    f"Checkpoint {name} expected health is invalid"
                ) from exc
        for field in (
            "telemetry_valid",
            "physics_residual_present",
            "ticket_created_this_tick",
        ):
            if field in expected and type(expected[field]) is not bool:
                raise ReferenceReplayError(
                    f"Checkpoint {name} expected {field} must be boolean"
                )
        if "active_ticket_count" in expected and (
            type(expected["active_ticket_count"]) is not int
            or expected["active_ticket_count"] < 0
        ):
            raise ReferenceReplayError(
                f"Checkpoint {name} expected active_ticket_count must be nonnegative"
            )
        if name in names or (previous is not None and timestamp <= previous):
            raise ReferenceReplayError("Checkpoint names must be unique and timestamps increasing")
        if timestamp < start or timestamp > end:
            raise ReferenceReplayError(f"Checkpoint {name} is outside the replay interval")
        names.add(name)
        previous = timestamp
    return value


def _phase_seconds(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ReferenceReplayError(f"{field} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ReferenceReplayError(f"{field} must be a finite number")
    return result


def _validate_timeline(
    manifest: Mapping[str, Any], timestamps: list[dt.datetime]
) -> None:
    timeline = manifest.get("timeline")
    if not isinstance(timeline, Mapping):
        raise ReferenceReplayError("manifest.timeline must be an object")
    _require_exact_keys(
        timeline,
        "manifest.timeline",
        frozenset({"start_utc", "end_utc"}),
    )
    start = _utc_timestamp(
        _require_string(timeline.get("start_utc"), "manifest.timeline.start_utc"),
        "manifest.timeline.start_utc",
    )
    end = _utc_timestamp(
        _require_string(timeline.get("end_utc"), "manifest.timeline.end_utc"),
        "manifest.timeline.end_utc",
    )
    if start != timestamps[0] or end != timestamps[-1]:
        raise ReferenceReplayError(
            "Manifest timeline must match the first and last actual records"
        )
    duration = (end - start).total_seconds()
    phases = manifest.get("phases")
    if not isinstance(phases, list) or not phases:
        raise ReferenceReplayError("manifest.phases must be a nonempty list")
    names: set[str] = set()
    previous_start = -math.inf
    for index, phase in enumerate(phases):
        if not isinstance(phase, Mapping):
            raise ReferenceReplayError(f"manifest.phases[{index}] must be an object")
        _require_exact_keys(
            phase,
            f"manifest.phases[{index}]",
            frozenset({"name", "start_seconds", "end_seconds"}),
        )
        name = _require_string(phase.get("name"), f"manifest.phases[{index}].name")
        if name not in _REFERENCE_PHASES or name in names:
            raise ReferenceReplayError("Manifest phase names must be known and unique")
        phase_start = _phase_seconds(
            phase.get("start_seconds"), f"manifest.phases[{index}].start_seconds"
        )
        phase_end = _phase_seconds(
            phase.get("end_seconds"), f"manifest.phases[{index}].end_seconds"
        )
        if not 0.0 <= phase_start <= phase_end <= duration:
            raise ReferenceReplayError(
                f"Manifest phase {name} must lie inside the dataset interval"
            )
        if phase_start < previous_start:
            raise ReferenceReplayError("Manifest phases must be ordered by start time")
        names.add(name)
        previous_start = phase_start
    if names != set(_REFERENCE_PHASES):
        raise ReferenceReplayError("Manifest must describe every reference phase exactly once")


def load_reference_replay(
    directory: str | Path = DEFAULT_REFERENCE_DIRECTORY,
) -> ReferenceReplayDataset:
    root = Path(directory)
    if not root.is_dir():
        raise ReferenceReplayError(f"Reference replay directory not found: {root}")
    entries = {
        path.name: path
        for path in root.iterdir()
        if path.name != "__pycache__"
    }
    if set(entries) != set(REFERENCE_DIRECTORY_FILES) or any(
        not path.is_file() for path in entries.values()
    ):
        raise ReferenceReplayError(
            "Reference replay resources must contain exactly the six frozen files and generator"
        )
    manifest = _validate_manifest(root)
    identity, station = _load_identity(manifest)
    dataset_id = str(manifest["dataset_id"])
    mapping = _load_mapping(
        root / "source_mapping.json",
        dataset_id=dataset_id,
        identity=identity,
        station=station,
    )
    samples = _load_telemetry(
        root / "telemetry.csv", identity=identity, mapping=mapping
    )
    contexts = _load_context(root / "context.csv", identity=identity)
    samples_by_time: dict[dt.datetime, list[TelemetrySample]] = {}
    for sample in samples:
        samples_by_time.setdefault(sample.timestamp, []).append(sample)
    context_by_time = {context.timestamp: context for context in contexts}
    timestamps = sorted(set(samples_by_time) | set(context_by_time))
    if not timestamps:
        raise ReferenceReplayError("Reference replay contains no timestamped records")
    _validate_timeline(manifest, timestamps)
    checkpoints = _load_checkpoints(
        root / "expected_checkpoints.json",
        dataset_id=dataset_id,
        station=station,
        start=timestamps[0],
        end=timestamps[-1],
    )
    batches = tuple(
        TelemetryBatch(
            tuple(samples_by_time.get(timestamp, ())),
            context_by_time.get(timestamp),
        )
        for timestamp in timestamps
    )
    source = _ValidatedReferenceReplaySource(
        identity,
        station,
        batches,
        origin=DataOrigin.SYNTHETIC,
    )
    return ReferenceReplayDataset(
        root,
        manifest,
        identity,
        station,
        source,
        len(samples),
        len(contexts),
        checkpoints,
    )


