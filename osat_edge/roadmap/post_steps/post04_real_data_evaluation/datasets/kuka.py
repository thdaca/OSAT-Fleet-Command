"""KUKA KR3 external component/process benchmark evaluation."""
from __future__ import annotations
import csv
import datetime as dt
import io
import math
from pathlib import Path
import re
import time
from typing import Any, Mapping
import zipfile
import numpy as np
from ....pre_steps.pre01_common.contracts import ChannelSpec, DataOrigin, EquipmentState, MachineIdentity, OperatingContext, TelemetrySample
from ....pre_steps.pre02_machine_registry.registry import StationDefinition
from ....pre_steps.pre03_data_provenance.provenance import (
    legacy_external_directory_hash as _directory_hash, md5_file as _md5_file,
    legacy_external_named_content_hash as _named_content_hash, sha256_file as _sha256_file,
)
from ....steps.step02_physical_features.features import FeatureSet, extract_physical_features
from ....steps.step07_machine_model.model import evaluate_machine_model_numerically
from ....steps.step08_live_telemetry.store import BoundedTelemetryStore, TelemetryStatus, assess_telemetry
from ..core.dataset_context import RealDataEvaluationError, RealDataNotFound, _base_report, _bounded_directory_files, _unverified_input
from ...metrics import _percentile, _spearman
from ..core.model_bridge import _fit_nominal_benchmark_model
KUKA_COLUMNS = {
    f"Iststrom_A{axis} (A)": (f"motor_current_a{axis}", f"axis_a{axis}")
    for axis in range(1, 7)
}
KUKA_TIME_COLUMN = "Sample"
KUKA_FILE = re.compile(r"collector_(?P<payload>[0-9]+)_(?P<split>[1-8])\.csv$")
MAXIMUM_KUKA_ARCHIVE_BYTES = 512 * 1024 * 1024
MAXIMUM_KUKA_MEMBERS = 1_000
MAXIMUM_KUKA_MEMBER_BYTES = 8 * 1024 * 1024
MAXIMUM_KUKA_TOTAL_BYTES = 512 * 1024 * 1024
MAXIMUM_KUKA_ROWS_PER_FILE = 100_000
KUKA_OFFICIAL_ARCHIVE_SHA256 = "51f93e8c453dd857170698627dc1d64ef14839e5c6efdb68148d01e0100c1253"
KUKA_OFFICIAL_ARCHIVE_MD5 = "efe9394bf2579f380832eed6d501c614"
KUKA_OFFICIAL_CSV_SET_SHA256 = "f3af97316d3366e0ac28f299025e36f4e9eeffc58e93c231f5a1c3b9ee4eeda4"
def _kuka_profile(robot: str) -> tuple[MachineIdentity, StationDefinition]:
    family = "external_kuka_kr3"
    station_id = f"KUKA-{robot}"
    identity = MachineIdentity(robot, family, station_id, f"KUKA KR3 {robot}")
    channels = tuple(
        ChannelSpec(
            name=target,
            unit="A",
            subsystem=subsystem,
            required=True,
            period_seconds=0.012,
            stale_seconds=5.0,
            source_id=source,
        )
        for source, (target, subsystem) in KUKA_COLUMNS.items()
    )
    return identity, StationDefinition(family, station_id, f"KUKA KR3 {robot}", channels)


def _canonical_kuka_name(name: str) -> str:
    parts = name.replace("\\", "/").strip("/").split("/")
    for index, part in enumerate(parts):
        if part in {"Robot_R1", "Robot_R2"}:
            return "/".join(parts[index:])
    return "/".join(parts)


def _kuka_readers(path: Path) -> tuple[str, str, str | None, list[tuple[str, bytes]]]:
    selected = path
    if path.is_dir():
        archives = sorted(path.glob("*.zip"))
        if len(archives) == 1:
            selected = archives[0]
        elif len(archives) > 1:
            raise RealDataEvaluationError("KUKA directory contains multiple ZIP archives")
    if selected.is_file():
        if selected.suffix.lower() != ".zip":
            raise RealDataEvaluationError("KUKA path must be the official ZIP or an extracted directory")
        if selected.stat().st_size > MAXIMUM_KUKA_ARCHIVE_BYTES:
            raise RealDataEvaluationError("KUKA archive exceeds the evaluation size limit")
        try:
            with zipfile.ZipFile(selected) as archive:
                members = [item for item in archive.infolist() if item.filename.lower().endswith(".csv")]
                if len(archive.infolist()) > MAXIMUM_KUKA_MEMBERS or not members:
                    raise RealDataEvaluationError("KUKA archive member count is invalid")
                if len({item.filename for item in archive.infolist()}) != len(archive.infolist()):
                    raise RealDataEvaluationError("KUKA archive contains duplicate member names")
                if sum(item.file_size for item in archive.infolist()) > MAXIMUM_KUKA_TOTAL_BYTES:
                    raise RealDataEvaluationError("KUKA archive expands beyond the size limit")
                rows: list[tuple[str, bytes]] = []
                for member in sorted(members, key=lambda value: value.filename):
                    if member.file_size > MAXIMUM_KUKA_MEMBER_BYTES:
                        raise RealDataEvaluationError("KUKA CSV exceeds the per-file size limit")
                    with archive.open(member) as stream:
                        content = stream.read(MAXIMUM_KUKA_MEMBER_BYTES + 1)
                    if len(content) != member.file_size:
                        raise RealDataEvaluationError("KUKA archive member size mismatch")
                    rows.append((member.filename, content))
        except zipfile.BadZipFile as exc:
            raise RealDataEvaluationError("KUKA ZIP is invalid") from exc
        canonical = [(_canonical_kuka_name(name), content) for name, content in rows]
        return _sha256_file(selected), _named_content_hash(canonical), _md5_file(selected), rows
    all_files = _bounded_directory_files(
        path,
        maximum_members=MAXIMUM_KUKA_MEMBERS,
        maximum_file_bytes=MAXIMUM_KUKA_MEMBER_BYTES,
        maximum_total_bytes=MAXIMUM_KUKA_TOTAL_BYTES,
    )
    files = [item for item in all_files if item.suffix.lower() == ".csv"]
    if not files:
        raise RealDataNotFound("KUKA CSV files not found")
    rows = [(item.relative_to(path).as_posix(), item.read_bytes()) for item in files]
    canonical = [(_canonical_kuka_name(name), content) for name, content in rows]
    return _directory_hash(path, files), _named_content_hash(canonical), None, rows


def _parse_kuka_file(name: str, content: bytes) -> tuple[str, int, int, np.ndarray, dict[str, np.ndarray]]:
    match = KUKA_FILE.search(Path(name).name)
    robot_match = re.search(r"Robot_(R[12])", name.replace("\\", "/"))
    if match is None or robot_match is None:
        raise RealDataEvaluationError(f"Unrecognized KUKA measurement identity {name!r}")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise RealDataEvaluationError("KUKA CSV must be UTF-8") from exc
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    expected = set(KUKA_COLUMNS) | {KUKA_TIME_COLUMN}
    if reader.fieldnames is None or set(reader.fieldnames) != expected:
        raise RealDataEvaluationError("KUKA CSV columns or ampere units do not match the official schema")
    timestamps: list[float] = []
    values = {target: [] for target, _ in KUKA_COLUMNS.values()}
    for index, row in enumerate(reader):
        if index >= MAXIMUM_KUKA_ROWS_PER_FILE:
            raise RealDataEvaluationError("KUKA CSV exceeds the row limit")
        try:
            timestamp = float(row[KUKA_TIME_COLUMN]) / 1000.0
            numeric = {
                target: float(row[source])
                for source, (target, _subsystem) in KUKA_COLUMNS.items()
            }
        except (TypeError, ValueError) as exc:
            raise RealDataEvaluationError("KUKA CSV contains a nonnumeric value") from exc
        if not math.isfinite(timestamp) or not all(math.isfinite(value) for value in numeric.values()):
            raise RealDataEvaluationError("KUKA CSV contains a nonfinite value")
        timestamps.append(timestamp)
        for target, value in numeric.items():
            values[target].append(value)
    time_array = np.asarray(timestamps, dtype=np.float64)
    if len(time_array) < 3 or not bool(np.all(np.diff(time_array) > 0.0)):
        raise RealDataEvaluationError("KUKA timestamps must contain three increasing samples")
    return (
        robot_match.group(1),
        int(match.group("payload")),
        int(match.group("split")),
        time_array,
        {name: np.asarray(items, dtype=np.float64) for name, items in values.items()},
    )


def _kuka_feature_set(
    identity: MachineIdentity,
    profile: StationDefinition,
    logical_start: dt.datetime,
    sample_time: np.ndarray,
    channel_values: Mapping[str, np.ndarray],
) -> tuple[FeatureSet, TelemetryStatus]:
    store = BoundedTelemetryStore(
        identity,
        profile,
        maximum_samples_per_channel=max(len(sample_time), 3),
        maximum_context_records=1,
    )
    # The source README declares 12 ms acquisition, while the Sample field
    # increments by values that look like 4 ms.  Use the declaration only to
    # construct a bounded window; timing-dependent Step 02 features are removed
    # below and never enter the benchmark model or headline score.
    declared_offsets = np.arange(len(sample_time), dtype=np.float64) * 0.012
    for spec in profile.channels:
        for offset, value in zip(declared_offsets, channel_values[spec.name], strict=True):
            store.append(
                TelemetrySample(
                    machine_id=identity.machine_id,
                    channel=spec.name,
                    timestamp=logical_start + dt.timedelta(seconds=float(offset)),
                    value=float(value),
                    unit=spec.unit,
                    source_id=spec.source_id,
                )
            )
    end = logical_start + dt.timedelta(seconds=float(declared_offsets[-1]))
    store.append_context(OperatingContext(identity.machine_id, end, EquipmentState.PROCESSING))
    duration = end - logical_start + dt.timedelta(microseconds=1)
    windows = store.windows([channel.name for channel in profile.channels], end=end, duration=duration)
    status = assess_telemetry(store, now=end, windows=windows)
    extracted = extract_physical_features(
        identity,
        profile,
        windows,
        timestamp=end,
        equipment_state=EquipmentState.PROCESSING,
        window_start=logical_start,
    )
    feature_set = FeatureSet(
        machine=extracted.machine,
        timestamp=extracted.timestamp,
        equipment_state=extracted.equipment_state,
        window_start=extracted.window_start,
        window_end=extracted.window_end,
        features=tuple(feature for feature in extracted.features if feature.kind != "trend"),
    )
    return feature_set, status
def _evaluate_kuka(path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    source_hash, content_hash, archive_md5, files = _kuka_readers(path)
    parsed = [_parse_kuka_file(name, content) for name, content in files]
    identities = [(robot, payload, split) for robot, payload, split, _time, _values in parsed]
    if len(identities) != len(set(identities)):
        raise RealDataEvaluationError("KUKA robot/payload/split identities must be unique")
    archive_identity_matches = (
        source_hash == KUKA_OFFICIAL_ARCHIVE_SHA256
        and archive_md5 == KUKA_OFFICIAL_ARCHIVE_MD5
    )
    content_identity_matches = content_hash == KUKA_OFFICIAL_CSV_SET_SHA256
    if not (archive_identity_matches or content_identity_matches):
        return _unverified_input(
            "kuka-kr3",
            source_hash,
            "The input schema is KUKA-compatible, but neither its archive identity nor its canonical CSV-set hash matches the pinned official v1 dataset.",
            runs=len(parsed),
            machines=len({item[0] for item in parsed}),
            observed_compatible_channels=6,
            canonical_content_sha256=content_hash,
            expected_official_archive_sha256=KUKA_OFFICIAL_ARCHIVE_SHA256,
            expected_official_archive_md5=KUKA_OFFICIAL_ARCHIVE_MD5,
            expected_official_csv_set_sha256=KUKA_OFFICIAL_CSV_SET_SHA256,
        )
    by_robot: dict[str, list[tuple[int, int, FeatureSet, TelemetryStatus]]] = {}
    base = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
    for robot, payload, split, sample_time, channel_values in parsed:
        identity, profile = _kuka_profile(robot)
        feature_set, status = _kuka_feature_set(
            identity,
            profile,
            base,
            sample_time,
            channel_values,
        )
        by_robot.setdefault(robot, []).append((payload, split, feature_set, status))

    machine_reports: list[dict[str, Any]] = []
    latencies: list[float] = []
    evaluated_windows = 0
    observable_windows = 0
    available_scores = 0
    all_scores: list[float] = []
    for robot, records in sorted(by_robot.items()):
        identity, _profile = _kuka_profile(robot)
        training_splits = {1, 2, 3} if robot == "R1" else {5, 6, 7}
        evaluation_splits = {4} if robot == "R1" else {8}
        training = [record for record in records if record[1] in training_splits]
        evaluation = [record for record in records if record[1] in evaluation_splits]
        if len(training) < 12:
            raise RealDataEvaluationError(
                f"KUKA {robot} needs at least 12 complete published-split nominal runs"
            )
        if not evaluation:
            raise RealDataEvaluationError(f"KUKA {robot} has no published-split held-out runs")
        train_sets = tuple(record[2] for record in training)
        model = _fit_nominal_benchmark_model(identity, train_sets)
        payloads: list[float] = []
        deviation_scores: list[float] = []
        for payload, _split, feature_set, status in sorted(evaluation, key=lambda item: item[0]):
            tick_started = time.perf_counter()
            result = evaluate_machine_model_numerically(model, identity, feature_set)
            latencies.append(time.perf_counter() - tick_started)
            evaluated_windows += 1
            observable_windows += int(status.valid and status.observable)
            available_scores += int(result.available)
            if result.available:
                score = max(deviation.score for deviation in result.deviations)
                payloads.append(float(payload))
                deviation_scores.append(score)
                all_scores.append(score)
        machine_reports.append(
            {
                "machine_id": identity.machine_id,
                "training_runs": len(training),
                "evaluation_runs": len(evaluation),
                "split": (
                    "D1-D3 nominal calibration / D4 evaluation"
                    if robot == "R1"
                    else "D5-D7 nominal calibration / D8 evaluation"
                ),
                "payload_deviation_spearman": _spearman(payloads, deviation_scores),
                "deviation_score_distribution": {
                    "count": len(deviation_scores),
                    "median": float(np.median(deviation_scores)) if deviation_scores else None,
                    "p95": _percentile(deviation_scores, 95.0),
                    "maximum": max(deviation_scores) if deviation_scores else None,
                },
            }
        )

    elapsed = time.perf_counter() - started
    report = _base_report(
        "kuka-kr3",
        source_hash,
        provenance_verified=True,
        provenance_method=(
            "pinned official v1 archive SHA-256 and MD5"
            if archive_identity_matches
            else "pinned canonical official v1 CSV-set SHA-256"
        ),
    )
    report.update(
        {
            "status": "EXECUTED",
            "official_version": "v1",
            "source_archive_md5": archive_md5,
            "canonical_content_sha256": content_hash,
            "mapped_channels": [
                {
                    "source": source,
                    "benchmark_channel": target,
                    "unit": "A",
                    "subsystem": subsystem,
                }
                for source, (target, subsystem) in KUKA_COLUMNS.items()
            ],
            "channel_coverage": {"mapped": 6, "total": 6, "fraction": 1.0},
            "source_field_coverage": {
                "mapped_physical_signals": 6,
                "total_fields_including_timestamp": 7,
                "fraction": 6.0 / 7.0,
            },
            "full_station_representation": False,
            "station_profile": "ephemeral external_kuka_kr3; canonical STATIONS unchanged",
            "split": "published same-machine split: R1 D1-D3 to D4; R2 D5-D7 to D8; whole files preserved",
            "samples": int(sum(len(item[3]) for item in parsed)),
            "runs": len(parsed),
            "machines": len(by_robot),
            "pipeline": {
                "bounded_store": True,
                "step02_run_statistics": True,
                "step02_timing_features": False,
                "step03_physics": False,
                "step05_family_model": False,
                "step07_numerical_deviation": True,
                "step09_health": False,
                "step10_evidence": False,
                "step15_ticket": False,
            },
            "method_scope": "partial Step02 location/spread and pure Step07 run-level numerical reuse; not end-to-end operational inference",
            "feature_kinds_used": ["location", "spread"],
            "timing_dependent_features_used": False,
            "nominal_baseline_semantics": "workload calibration only; not confirmed healthy history",
            "metrics_supported": [
                "run-level deviation-score distributions",
                "payload/deviation rank association",
                "pipeline coverage",
                "throughput and latency",
            ],
            "classification_metrics": None,
            "classification_metrics_reason": "The payload dataset has no health/fault labels; accuracy and confusion metrics are unsupported.",
            "deviation_score_distribution": {
                "count": len(all_scores),
                "median": float(np.median(all_scores)) if all_scores else None,
                "p95": _percentile(all_scores, 95.0),
                "maximum": max(all_scores) if all_scores else None,
            },
            "data_quality_coverage": observable_windows / evaluated_windows,
            "pipeline_coverage": available_scores / evaluated_windows,
            "runtime": {
                "elapsed_seconds": elapsed,
                "windows_per_second": evaluated_windows / elapsed if elapsed > 0.0 else None,
                "mean_tick_latency_ms": 1000.0 * float(np.mean(latencies)),
                "p95_tick_latency_ms": 1000.0 * float(np.percentile(latencies, 95.0)),
            },
            "machine_results": machine_reports,
            "limitations": [
                "Evidence class D component/process analog; not semiconductor or OSAT validation.",
                "The dataset contains payload variation but no fault or independently adjudicated health labels.",
                "Calibration files form a benchmark-only nominal baseline, not confirmed healthy equipment history.",
                "The README states a 12 ms sampling period while Sample increments resemble 4 ms; trend features are excluded from every score until that discrepancy is resolved.",
                "Each CSV is one independent run-level window, not an operational 60-second feature window.",
                "Independent recordings have no asserted cross-run chronology, so Steps 09 and 10 are not run and no health-state distribution is reported.",
                "No KUKA signal is substituted for an OSAT station channel, and no physics relation is available for this ephemeral family.",
            ],
        }
    )
    return report
