"""Frozen synthetic reference replay through the operational PHM pipeline."""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import math
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .common import (
    DataOrigin,
    EquipmentState,
    MachineIdentity,
    OperatingContext,
    RuntimeMode,
    TelemetrySample,
    VERSION,
)
from .demo import _fit_demo_model
from .machines import STATIONS, StationDefinition
from .pipeline import MachinePipeline, PipelineResult
from .roadmap.step08_live_telemetry import ReplayTelemetrySource, TelemetryBatch
from .roadmap.step11a_maintenance_db import MaintenanceRepository
from .roadmap.step11b_oem_manuals import load_oem_manuals
from .roadmap.step15_maintenance_ticket import list_tickets


REFERENCE_SCHEMA_VERSION = "1.0"
REFERENCE_DATASET_ID = "osat-reference-fleet-001"
REFERENCE_FILES = (
    "telemetry.csv",
    "context.csv",
    "source_mapping.json",
    "expected_checkpoints.json",
)
DEFAULT_REFERENCE_DIRECTORY = (
    Path(__file__).resolve().parent.parent / "examples" / "reference_replay"
)
_DATASET_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,79}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


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


def _validate_manifest(directory: Path) -> Mapping[str, Any]:
    path = directory / "manifest.json"
    if not path.is_file():
        raise ReferenceReplayError("Reference replay manifest.json is missing")
    manifest = _read_json(path)
    dataset_id = _require_string(manifest.get("dataset_id"), "manifest.dataset_id")
    if not _DATASET_ID.fullmatch(dataset_id):
        raise ReferenceReplayError("manifest.dataset_id has an invalid format")
    if dataset_id != REFERENCE_DATASET_ID:
        raise ReferenceReplayError("Unsupported reference replay dataset_id")
    if manifest.get("schema_version") != REFERENCE_SCHEMA_VERSION:
        raise ReferenceReplayError("Unsupported reference replay schema_version")
    if manifest.get("release_version") != VERSION:
        raise ReferenceReplayError("Reference replay release_version does not match the runtime")
    if manifest.get("origin") != DataOrigin.SYNTHETIC.value:
        raise ReferenceReplayError("Reference replay origin must be SYNTHETIC")
    if manifest.get("runtime_mode") != RuntimeMode.REAL_REPLAY.value:
        raise ReferenceReplayError("Reference replay runtime_mode must be REAL_REPLAY")
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
            rows = list(reader)
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
    path: Path, *, dataset_id: str, start: dt.datetime, end: dt.datetime
) -> Mapping[str, Any]:
    value = _read_json(path)
    if value.get("schema_version") != REFERENCE_SCHEMA_VERSION:
        raise ReferenceReplayError("Unsupported expected-checkpoint schema_version")
    if value.get("dataset_id") != dataset_id:
        raise ReferenceReplayError("Expected checkpoints belong to another dataset")
    rows = value.get("checkpoints")
    if not isinstance(rows, list) or not rows:
        raise ReferenceReplayError("Expected checkpoints require a nonempty list")
    names: set[str] = set()
    previous: dt.datetime | None = None
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ReferenceReplayError(f"Checkpoint {index} must be an object")
        name = _require_string(row.get("name"), f"checkpoints[{index}].name")
        timestamp = _utc_timestamp(
            _require_string(row.get("timestamp_utc"), f"checkpoints[{index}].timestamp_utc"),
            f"checkpoints[{index}].timestamp_utc",
        )
        expected = row.get("expected")
        if not isinstance(expected, Mapping) or not expected:
            raise ReferenceReplayError(f"Checkpoint {name} requires expected observations")
        if name in names or (previous is not None and timestamp <= previous):
            raise ReferenceReplayError("Checkpoint names must be unique and timestamps increasing")
        if timestamp < start or timestamp > end:
            raise ReferenceReplayError(f"Checkpoint {name} is outside the replay interval")
        names.add(name)
        previous = timestamp
    return value


def load_reference_replay(
    directory: str | Path = DEFAULT_REFERENCE_DIRECTORY,
) -> ReferenceReplayDataset:
    root = Path(directory)
    if not root.is_dir():
        raise ReferenceReplayError(f"Reference replay directory not found: {root}")
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
    checkpoints = _load_checkpoints(
        root / "expected_checkpoints.json",
        dataset_id=dataset_id,
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


def _checkpoint_observation(result: PipelineResult) -> dict[str, Any]:
    relation_name = "spindle.electromechanical_load_residual_a.median"
    residual = None
    if result.feature_set is not None:
        feature = result.feature_set.by_name.get(relation_name)
        if feature is not None:
            residual = feature.value
    return {
        "health": result.assessment.health_state.value,
        "telemetry_valid": result.telemetry_status.valid,
        "observable": result.telemetry_status.observable,
        "physics_residual_present": residual is not None,
        "physics_residual_a": residual,
        "ticket_created": result.ticket is not None,
    }


def run_reference_replay(
    directory: str | Path = DEFAULT_REFERENCE_DIRECTORY,
    *,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Run the frozen artifact. Expected checkpoints never influence inference."""

    dataset = load_reference_replay(directory)
    temporary: tempfile.TemporaryDirectory[str] | None = None
    if database_path is None:
        temporary = tempfile.TemporaryDirectory(prefix="osat-reference-replay-")
        database_path = Path(temporary.name) / "reference-tickets.sqlite"
    repository = MaintenanceRepository(database_path)
    manuals = load_oem_manuals(
        Path(__file__).resolve().parent.parent / "knowledge" / "maintenance_playbooks.json"
    )
    model = _fit_demo_model(dataset.identity, dataset.station)
    pipeline = MachinePipeline(
        identity=dataset.identity,
        station=dataset.station,
        source=dataset.source,
        repository=repository,
        manual_chunks=manuals,
        machine_model=model,
    )
    expected_by_time = {
        _utc_timestamp(str(row["timestamp_utc"]), "checkpoint timestamp"): str(row["name"])
        for row in dataset.expected_checkpoints["checkpoints"]
    }
    checkpoints: dict[str, dict[str, Any]] = {}
    health_counts: dict[str, int] = {}
    valid_ticks = 0
    invalid_ticks = 0
    residual_ticks = 0
    abstention_ticks = 0
    positive_residual_ticks = 0
    maximum_residual: float | None = None
    last: PipelineResult | None = None
    tick_count = 0
    try:
        while True:
            result = pipeline.tick()
            if result is None:
                break
            last = result
            tick_count += 1
            state = result.assessment.health_state.value
            health_counts[state] = health_counts.get(state, 0) + 1
            if result.telemetry_status.valid:
                valid_ticks += 1
            else:
                invalid_ticks += 1
            relation = None
            if result.feature_set is not None:
                relation = result.feature_set.by_name.get(
                    "spindle.electromechanical_load_residual_a.median"
                )
                if relation is None:
                    abstention_ticks += 1
                else:
                    residual_ticks += 1
                    if relation.value > 0.0:
                        positive_residual_ticks += 1
                    maximum_residual = (
                        relation.value
                        if maximum_residual is None
                        else max(maximum_residual, relation.value)
                    )
            checkpoint_name = expected_by_time.get(result.assessment.timestamp)
            if checkpoint_name is not None:
                checkpoints[checkpoint_name] = _checkpoint_observation(result)
        if last is None:
            raise ReferenceReplayError("Reference replay produced no pipeline result")
        tickets = list_tickets(repository)
        return {
            "version": VERSION,
            "dataset_id": dataset.manifest["dataset_id"],
            "schema_version": dataset.manifest["schema_version"],
            "origin": DataOrigin.SYNTHETIC.value,
            "runtime_mode": RuntimeMode.REAL_REPLAY.value,
            "machine_id": dataset.identity.machine_id,
            "family": dataset.identity.family,
            "station_id": dataset.identity.station_id,
            "telemetry_rows": dataset.telemetry_rows,
            "context_rows": dataset.context_rows,
            "ticks": tick_count,
            "valid_ticks": valid_ticks,
            "invalid_ticks": invalid_ticks,
            "health_counts": health_counts,
            "physics_residual_ticks": residual_ticks,
            "physics_abstention_ticks": abstention_ticks,
            "positive_residual_ticks": positive_residual_ticks,
            "maximum_positive_residual_a": maximum_residual,
            "checkpoint_observations": checkpoints,
            "tickets": [ticket.to_payload() for ticket in tickets],
            "final_health": last.assessment.health_state.value,
            "model_source": "deterministic synthetic healthy calibration using the existing demo calibration path",
            "claims": [
                "SYNTHETIC REFERENCE REPLAY",
                "DEVELOPMENT-ONLY RESEARCH PIPELINE DEMONSTRATION",
                "NOT REAL OSAT DATA",
                "NOT PLANT VALIDATION",
                "NOT PRODUCTION QUALIFICATION",
            ],
        }
    finally:
        if temporary is not None:
            temporary.cleanup()
