"""Isolated, offline evaluation of explicitly identified external real data.

This module may reuse Steps 02, 07, 09, and 10 where the source semantics make
that defensible.  It never imports or calls Step 15 and never attaches an
external model to an operational pipeline.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import math
from pathlib import Path
import re
import time
from typing import Any, Mapping, Sequence
import zipfile

import numpy as np

from .benchmark import BenchmarkError, analyze_nasa_milling
from .common import (
    ChannelSpec,
    DataOrigin,
    EquipmentState,
    HealthState,
    MachineIdentity,
    OperatingContext,
    RuntimeMode,
    TelemetrySample,
    VERSION,
)
from .machines import StationDefinition
from .roadmap.step02_physical_features import FeatureSet, extract_physical_features
from .roadmap.step06_machine_history import HealthyInterval, MachineHistory
from .roadmap.step07_machine_model import (
    evaluate_machine_model_numerically,
    fit_machine_model,
)
from .roadmap.step08_live_telemetry import (
    BoundedTelemetryStore,
    TelemetryStatus,
    assess_telemetry,
)
from .roadmap.step09_health_risk import HealthEngine
from .roadmap.step10_fault_evidence import build_fault_evidence


DATASET_ORDER = (
    "wafer-dicing-chang-2024",
    "phm-2018-ion-mill",
    "phm-2016-cmp",
    "forinfpro-himd",
    "r2r-web-tension",
    "me-ad",
    "kuka-kr3",
    "rddac",
    "nasa-milling",
    "uci-secom",
)

DATASETS: dict[str, dict[str, str]] = {
    "wafer-dicing-chang-2024": {
        "title": "Chang/Tsai/Mo wafer-dicing study data",
        "source": "https://doi.org/10.3390/electronics13101802",
        "evidence_class": "A",
        "domain": "wafer dicing / chipping",
    },
    "phm-2018-ion-mill": {
        "title": "PHM Society 2018 Ion Mill Etch Data Challenge",
        "source": "https://phmsociety.org/conference/annual-conference-of-the-phm-society/annual-conference-of-the-prognostics-and-health-management-society-2018-b/phm-data-challenge-6/",
        "evidence_class": "B",
        "domain": "wafer-fabrication ion mill etch",
    },
    "phm-2016-cmp": {
        "title": "PHM Society 2016 Wafer CMP Data Challenge",
        "source": "https://phmsociety.org/conference/annual-conference-of-the-phm-society/annual-conference-of-the-prognostics-and-health-management-society-2016/phm-data-challenge-4/",
        "evidence_class": "B",
        "domain": "wafer-fabrication chemical-mechanical planarization",
    },
    "forinfpro-himd": {
        "title": "FORinFPRO-HIMD",
        "source": "https://doi.org/10.5281/zenodo.20744054",
        "evidence_class": "C",
        "domain": "hybrid injection molding",
    },
    "r2r-web-tension": {
        "title": "R2R Web Tension",
        "source": "https://doi.org/10.17632/gz3rzw6xgf.2",
        "evidence_class": "C",
        "domain": "roll-to-roll web transport",
    },
    "me-ad": {
        "title": "ME-AD Progressive Robotics Anomaly Detection",
        "source": "https://doi.org/10.5281/zenodo.20817531",
        "evidence_class": "C",
        "domain": "industrial robot progressive actuator degradation",
    },
    "kuka-kr3": {
        "title": "KUKA KR3 Motor-Current Dataset",
        "source": "https://doi.org/10.5281/zenodo.21456277",
        "evidence_class": "D",
        "domain": "industrial robot motor current / payload",
    },
    "rddac": {
        "title": "RDDAC Real Deep Drawing and Cutting Dataset",
        "source": "https://doi.org/10.18419/DARUS-5589",
        "evidence_class": "C",
        "domain": "forming and cutting",
    },
    "nasa-milling": {
        "title": "NASA/UC Berkeley Milling Data Set",
        "source": "https://data.nasa.gov/dataset/milling-wear",
        "evidence_class": "C",
        "domain": "milling / machining",
    },
    "uci-secom": {
        "title": "UCI SECOM",
        "source": "https://doi.org/10.24432/C54305",
        "evidence_class": "B",
        "domain": "semiconductor manufacturing process / yield",
    },
}

KUKA_COLUMNS = {
    f"Iststrom_A{axis} (A)": (f"motor_current_a{axis}", f"axis_a{axis}")
    for axis in range(1, 7)
}
KUKA_TIME_COLUMN = "Sample"
KUKA_FILE = re.compile(r"collector_(?P<payload>[0-9]+)_(?P<split>[1-8])\.csv$")
MAXIMUM_KUKA_ARCHIVE_BYTES = 512 * 1024 * 1024
MAXIMUM_KUKA_MEMBERS = 1_000
MAXIMUM_KUKA_MEMBER_BYTES = 8 * 1024 * 1024
MAXIMUM_KUKA_ROWS_PER_FILE = 100_000
MAXIMUM_GENERIC_ARCHIVE_BYTES = 256 * 1024 * 1024
MAXIMUM_GENERIC_MEMBERS = 1_000
MAXIMUM_GENERIC_MEMBER_BYTES = 64 * 1024 * 1024
MAXIMUM_GENERIC_TOTAL_BYTES = 256 * 1024 * 1024


class RealDataEvaluationError(ValueError):
    pass


class RealDataNotFound(RealDataEvaluationError):
    pass


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _directory_hash(path: Path, files: Sequence[Path]) -> str:
    digest = hashlib.sha256()
    for item in sorted(files, key=lambda value: value.relative_to(path).as_posix()):
        name = item.relative_to(path).as_posix().encode("utf-8")
        digest.update(len(name).to_bytes(4, "big"))
        digest.update(name)
        with item.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    return digest.hexdigest()


def _base_report(dataset_id: str, source_hash: str | None) -> dict[str, Any]:
    metadata = DATASETS[dataset_id]
    return {
        "version": VERSION,
        "dataset": dataset_id,
        "title": metadata["title"],
        "source": metadata["source"],
        "source_sha256": source_hash,
        "origin": DataOrigin.EXTERNAL_BENCHMARK.value,
        "real_data": True,
        "synthetic_data": False,
        "evidence_class": metadata["evidence_class"],
        "domain": metadata["domain"],
        "osat_plant_validation": False,
        "production_qualified": False,
        "ticket_authority": False,
        "operational_ticket_count": 0,
        "step15_called": False,
    }


def _unavailable(dataset_id: str, reason: str) -> dict[str, Any]:
    report = _base_report(dataset_id, None)
    report.update(
        {
            "status": "UNAVAILABLE",
            "mapped_channels": [],
            "channel_coverage": {"mapped": 0, "total": 0, "fraction": None},
            "full_station_representation": False,
            "limitations": [reason],
        }
    )
    return report


def _average_ranks(values: Sequence[float]) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    order = np.argsort(array, kind="mergesort")
    result = np.empty(len(array), dtype=np.float64)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and array[order[end]] == array[order[start]]:
            end += 1
        result[order[start:end]] = (start + end - 1) / 2.0
        start = end
    return result


def _spearman(first: Sequence[float], second: Sequence[float]) -> float | None:
    if len(first) < 3 or len(first) != len(second):
        return None
    ranked_first = _average_ranks(first)
    ranked_second = _average_ranks(second)
    if float(np.std(ranked_first)) == 0.0 or float(np.std(ranked_second)) == 0.0:
        return None
    return float(np.corrcoef(ranked_first, ranked_second)[0, 1])


def _percentile(values: Sequence[float], percentile: float) -> float | None:
    if not values:
        return None
    return float(np.percentile(np.asarray(values, dtype=np.float64), percentile))


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


def _kuka_readers(path: Path) -> tuple[str, list[tuple[str, bytes]]]:
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
        return _sha256_file(selected), rows
    files = sorted(path.rglob("*.csv"))
    if not files:
        raise RealDataNotFound("KUKA CSV files not found")
    return _directory_hash(path, files), [
        (item.relative_to(path).as_posix(), item.read_bytes()) for item in files
    ]


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
    start_value = float(sample_time[0])
    for spec in profile.channels:
        for offset, value in zip(sample_time - start_value, channel_values[spec.name], strict=True):
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
    end = logical_start + dt.timedelta(seconds=float(sample_time[-1] - start_value))
    store.append_context(OperatingContext(identity.machine_id, end, EquipmentState.PROCESSING))
    duration = end - logical_start + dt.timedelta(microseconds=1)
    windows = store.windows([channel.name for channel in profile.channels], end=end, duration=duration)
    status = assess_telemetry(store, now=end, windows=windows)
    feature_set = extract_physical_features(
        identity,
        profile,
        windows,
        timestamp=end,
        equipment_state=EquipmentState.PROCESSING,
        window_start=logical_start,
    )
    return feature_set, status


def _evaluate_kuka(path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    source_hash, files = _kuka_readers(path)
    parsed = [_parse_kuka_file(name, content) for name, content in files]
    identities = [(robot, payload, split) for robot, payload, split, _time, _values in parsed]
    if len(identities) != len(set(identities)):
        raise RealDataEvaluationError("KUKA robot/payload/split identities must be unique")
    by_robot: dict[str, list[tuple[int, int, FeatureSet, TelemetryStatus]]] = {}
    base = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
    for index, (robot, payload, split, sample_time, channel_values) in enumerate(parsed):
        identity, profile = _kuka_profile(robot)
        feature_set, status = _kuka_feature_set(
            identity,
            profile,
            base + dt.timedelta(minutes=index * 2),
            sample_time,
            channel_values,
        )
        by_robot.setdefault(robot, []).append((payload, split, feature_set, status))

    machine_reports: list[dict[str, Any]] = []
    total_states: dict[str, int] = {state.value: 0 for state in HealthState}
    latencies: list[float] = []
    evidence_records = 0
    evaluated_windows = 0
    observable_windows = 0
    available_scores = 0
    all_scores: list[float] = []
    for robot, records in sorted(by_robot.items()):
        identity, profile = _kuka_profile(robot)
        training = [record for record in records if record[1] in {1, 2, 5, 6}]
        evaluation = [record for record in records if record[1] in {3, 4, 7, 8}]
        if len(training) < 12:
            raise RealDataEvaluationError(
                f"KUKA {robot} needs at least 12 complete D1/D2 or D5/D6 training runs"
            )
        if not evaluation:
            raise RealDataEvaluationError(f"KUKA {robot} has no held-out D3/D4 or D7/D8 runs")
        train_sets = tuple(record[2] for record in training)
        interval = HealthyInterval(
            identity.machine_id,
            min(row.window_start for row in train_sets) - dt.timedelta(microseconds=1),
            max(row.window_end for row in train_sets) + dt.timedelta(microseconds=1),
        )
        model = fit_machine_model(
            MachineHistory(identity, DataOrigin.EXTERNAL_BENCHMARK, train_sets, (interval,))
        )
        engine = HealthEngine(identity, profile)
        payloads: list[float] = []
        risk_scores: list[float] = []
        robot_states: dict[str, int] = {state.value: 0 for state in HealthState}
        for payload, _split, feature_set, status in sorted(
            evaluation, key=lambda item: item[2].timestamp
        ):
            tick_started = time.perf_counter()
            result = evaluate_machine_model_numerically(model, identity, feature_set)
            assessment = engine.assess(
                status,
                result,
                timestamp=feature_set.timestamp,
                runtime_mode=RuntimeMode.REAL_REPLAY,
                equipment_state=feature_set.equipment_state,
            )
            evidence = build_fault_evidence(assessment)
            latencies.append(time.perf_counter() - tick_started)
            evaluated_windows += 1
            observable_windows += int(status.valid and status.observable)
            available_scores += int(result.available)
            evidence_records += int(evidence is not None)
            robot_states[assessment.health_state.value] += 1
            total_states[assessment.health_state.value] += 1
            if result.available:
                score = max(deviation.score for deviation in result.deviations)
                payloads.append(float(payload))
                risk_scores.append(score)
                all_scores.append(score)
        machine_reports.append(
            {
                "machine_id": identity.machine_id,
                "training_runs": len(training),
                "evaluation_runs": len(evaluation),
                "split": "D1-D2 train / D3-D4 evaluate" if robot == "R1" else "D5-D6 train / D7-D8 evaluate",
                "state_distribution": robot_states,
                "payload_score_spearman": _spearman(payloads, risk_scores),
            }
        )

    elapsed = time.perf_counter() - started
    report = _base_report("kuka-kr3", source_hash)
    report.update(
        {
            "status": "EXECUTED",
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
            "split": "whole-file, robot-preserving predefined D-set split; no sample-level leakage",
            "samples": int(sum(len(item[3]) for item in parsed)),
            "runs": len(parsed),
            "machines": len(by_robot),
            "pipeline": {
                "bounded_store": True,
                "step02_features": True,
                "step03_physics": False,
                "step05_family_model": False,
                "step07_exact_machine_score": True,
                "step09_health": True,
                "step10_evidence": True,
                "step15_ticket": False,
            },
            "metrics_supported": [
                "state and score distributions",
                "payload/score rank association",
                "UNKNOWN fraction",
                "pipeline coverage",
                "throughput and latency",
            ],
            "classification_metrics": None,
            "classification_metrics_reason": "The payload dataset has no health/fault labels; accuracy and confusion metrics are unsupported.",
            "state_distribution": total_states,
            "score_distribution": {
                "count": len(all_scores),
                "median": float(np.median(all_scores)) if all_scores else None,
                "p95": _percentile(all_scores, 95.0),
                "maximum": max(all_scores) if all_scores else None,
            },
            "unknown_fraction": total_states[HealthState.UNKNOWN.value] / evaluated_windows,
            "data_quality_coverage": observable_windows / evaluated_windows,
            "pipeline_coverage": available_scores / evaluated_windows,
            "fault_evidence_records": evidence_records,
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
                "Baseline files are treated as nominal research calibration, not proven healthy equipment history.",
                "The README states a 12 ms sampling period while the Sample values advance by 4 ms; source values are used as documented timestamps and the discrepancy is retained as a limitation.",
                "No KUKA signal is substituted for an OSAT station channel, and no physics relation is available for this ephemeral family.",
            ],
        }
    )
    return report


def _zip_members(path: Path) -> tuple[str, dict[str, bytes]]:
    if not path.exists():
        raise RealDataNotFound(f"Dataset path not found: {path.name}")
    selected = path
    if path.is_dir():
        archives = sorted(path.glob("*.zip"))
        if len(archives) == 1:
            selected = archives[0]
    if selected.is_file() and selected.suffix.lower() == ".zip":
        if selected.stat().st_size > MAXIMUM_GENERIC_ARCHIVE_BYTES:
            raise RealDataEvaluationError("Dataset ZIP exceeds the evaluation size limit")
        try:
            with zipfile.ZipFile(selected) as archive:
                files = [item for item in archive.infolist() if not item.is_dir()]
                if len(files) > MAXIMUM_GENERIC_MEMBERS:
                    raise RealDataEvaluationError("Dataset ZIP contains too many members")
                if any(item.file_size > MAXIMUM_GENERIC_MEMBER_BYTES for item in files):
                    raise RealDataEvaluationError("Dataset ZIP member exceeds the size limit")
                if sum(item.file_size for item in files) > MAXIMUM_GENERIC_TOTAL_BYTES:
                    raise RealDataEvaluationError("Dataset ZIP expands beyond the size limit")
                members = {}
                for item in files:
                    with archive.open(item) as stream:
                        content = stream.read(MAXIMUM_GENERIC_MEMBER_BYTES + 1)
                    if len(content) != item.file_size:
                        raise RealDataEvaluationError("Dataset ZIP member size mismatch")
                    members[item.filename] = content
        except zipfile.BadZipFile as exc:
            raise RealDataEvaluationError("Dataset ZIP is invalid") from exc
        return _sha256_file(selected), members
    files = sorted(path.rglob("*")) if path.is_dir() else [path]
    files = [item for item in files if item.is_file()]
    return _directory_hash(path, files), {
        item.relative_to(path).as_posix(): item.read_bytes() for item in files
    }


def _evaluate_secom(path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    source_hash, members = _zip_members(path)
    data_items = [(name, value) for name, value in members.items() if name.lower().endswith("secom.data")]
    label_items = [(name, value) for name, value in members.items() if name.lower().endswith("secom_labels.data")]
    if len(data_items) != 1 or len(label_items) != 1:
        raise RealDataEvaluationError("SECOM input must contain one data and one label file")
    try:
        data_lines = data_items[0][1].decode("utf-8").splitlines()
        label_lines = label_items[0][1].decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise RealDataEvaluationError("SECOM files must be UTF-8 text") from exc
    if not data_lines or len(data_lines) != len(label_lines):
        raise RealDataEvaluationError("SECOM data and labels must contain aligned nonempty rows")
    widths = {len(line.split()) for line in data_lines}
    if len(widths) != 1:
        raise RealDataEvaluationError("SECOM rows must have one feature width")
    labels: list[int] = []
    for line in label_lines:
        parts = line.split(maxsplit=1)
        if not parts or parts[0] not in {"-1", "1"}:
            raise RealDataEvaluationError("SECOM labels must be -1 or 1")
        labels.append(int(parts[0]))
    report = _base_report("uci-secom", source_hash)
    report.update(
        {
            "status": "INSPECTED_NOT_EXECUTABLE",
            "mapped_channels": [],
            "channel_coverage": {"mapped": 0, "total": next(iter(widths)), "fraction": 0.0},
            "full_station_representation": False,
            "samples": len(data_lines),
            "runs": None,
            "machines": None,
            "label_counts": {"pass": labels.count(-1), "fail": labels.count(1)},
            "classification_metrics": None,
            "runtime": {"elapsed_seconds": time.perf_counter() - started},
            "limitations": [
                "Evidence class B other semiconductor process/yield data; not equipment-health or OSAT plant validation.",
                "All sensor variables are anonymized and have no physical names or units, so zero channels can be mapped exactly.",
                "Pass/fail yield labels cannot be relabeled as equipment health or maintenance faults.",
                "No accuracy is reported because the unchanged PHM pipeline cannot execute without fabricated channel semantics.",
            ],
        }
    )
    return report


def _evaluate_forinfpro(path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    files = sorted(path.rglob("*.csv")) if path.is_dir() else [path]
    if not files or any(not item.exists() for item in files):
        raise RealDataNotFound("FORinFPRO-HIMD CSV files not found")
    schemas: list[dict[str, Any]] = []
    for item in files:
        with item.open("r", encoding="utf-8-sig", newline="") as stream:
            first = stream.readline()
            delimiter = ";" if first.count(";") > first.count(",") else ","
            stream.seek(0)
            reader = csv.reader(stream, delimiter=delimiter)
            header = tuple(value.strip() for value in (next(reader, None) or ()) if value.strip())
            count = sum(1 for _row in reader)
        signals = tuple(
            value
            for value in header
            if value.casefold() not in {"time", "datum/zeit", "maschinennummer"}
        )
        schemas.append(
            {
                "file": item.name,
                "declared_columns": len(header),
                "candidate_signal_columns": len(signals),
                "rows": count,
            }
        )
    report = _base_report("forinfpro-himd", _directory_hash(path, files) if path.is_dir() else _sha256_file(path))
    report.update(
        {
            "status": "INSPECTED_NOT_EXECUTABLE",
            "mapped_channels": [],
            "channel_coverage": {
                "mapped": 0,
                "total": sum(item["candidate_signal_columns"] for item in schemas),
                "fraction": 0.0,
            },
            "full_station_representation": False,
            "files": schemas,
            "classification_metrics": None,
            "runtime": {"elapsed_seconds": time.perf_counter() - started},
            "limitations": [
                "Evidence class C industrial mechanism analog; polymer injection molding is not semiconductor transfer molding.",
                "The inspected CSV headers do not declare physical units, so cavity pressure and temperature cannot be mapped to unit-enforced channels without guessing.",
                "Only one published cycle was present locally, so a disjoint exact-machine calibration/evaluation split is unavailable.",
            ],
        }
    )
    return report


def _evaluate_nasa(path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    selected = path
    if path.is_dir():
        archives = sorted(path.glob("*.zip"))
        mats = sorted(path.rglob("mill.mat"))
        if len(archives) == 1 and not mats:
            selected = archives[0]
    try:
        source = analyze_nasa_milling(selected)
    except BenchmarkError as exc:
        raise RealDataEvaluationError(str(exc)) from exc
    report = _base_report("nasa-milling", source["source_artifact_sha256"])
    report.update(
        {
            "status": "EXECUTED_DESCRIPTIVE",
            "mapped_channels": [],
            "channel_coverage": {"mapped": 0, "total": 3, "fraction": 0.0},
            "full_station_representation": False,
            "samples": None,
            "runs": source["runs"],
            "machines": None,
            "split": "none; descriptive association only",
            "metrics_supported": ["continuous wear rank association", "runtime"],
            "classification_metrics": None,
            "continuous_metrics": source["overall_descriptive_association"],
            "runtime": {"elapsed_seconds": time.perf_counter() - started},
            "limitations": [
                "Evidence class C machining analog; not semiconductor or OSAT validation.",
                "Signal output units are not documented and no spindle-speed time series exists, so Step 02/03/07/09 cannot be entered without fabrication.",
                "Wear correlations are descriptive associations and not failure probabilities, health labels, or causal effects.",
            ],
        }
    )
    return report


def _inspect_unmapped(dataset_id: str, path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RealDataNotFound(f"Dataset path not found: {path.name}")
    files = [path] if path.is_file() else [item for item in path.rglob("*") if item.is_file()]
    if not files:
        raise RealDataNotFound("No local dataset artifact was present.")
    source_hash = _sha256_file(path) if path.is_file() else _directory_hash(path, files)
    report = _base_report(dataset_id, source_hash)
    report.update(
        {
            "status": "INSPECTED_NOT_EXECUTABLE",
            "mapped_channels": [],
            "channel_coverage": {"mapped": 0, "total": 0, "fraction": None},
            "full_station_representation": False,
            "files": len(files),
            "classification_metrics": None,
            "limitations": [
                "No reviewed, semantically exact source-ID/channel/unit mapping is implemented for this dataset.",
                "The unchanged PHM pipeline was not run; no proxy signals or labels were fabricated.",
            ],
        }
    )
    return report


def evaluate_real_dataset(dataset_id: str, path: str | Path) -> dict[str, Any]:
    """Evaluate one explicit local external dataset without operational authority."""

    if dataset_id not in DATASETS:
        raise RealDataEvaluationError(f"Unknown external dataset {dataset_id!r}")
    selected = Path(path)
    if not selected.exists():
        raise RealDataNotFound(f"Dataset path not found: {selected.name}")
    if dataset_id == "kuka-kr3":
        return _evaluate_kuka(selected)
    if dataset_id == "nasa-milling":
        return _evaluate_nasa(selected)
    if dataset_id == "uci-secom":
        return _evaluate_secom(selected)
    if dataset_id == "forinfpro-himd":
        return _evaluate_forinfpro(selected)
    return _inspect_unmapped(dataset_id, selected)


def evaluate_all_real_data(root: str | Path) -> dict[str, Any]:
    """Attempt every registered dataset in the specified ignored/local root."""

    base = Path(root)
    reports: list[dict[str, Any]] = []
    for dataset_id in DATASET_ORDER:
        candidate = base / dataset_id
        if not candidate.exists():
            reports.append(_unavailable(dataset_id, "No local dataset artifact was present."))
            continue
        try:
            reports.append(evaluate_real_dataset(dataset_id, candidate))
        except RealDataEvaluationError as exc:
            reports.append(_unavailable(dataset_id, str(exc)))
    return {
        "version": VERSION,
        "origin": DataOrigin.EXTERNAL_BENCHMARK.value,
        "dataset_order": list(DATASET_ORDER),
        "datasets": reports,
        "summary": {
            "attempted": len(reports),
            "executed": sum(report["status"].startswith("EXECUTED") for report in reports),
            "inspected_not_executable": sum(report["status"] == "INSPECTED_NOT_EXECUTABLE" for report in reports),
            "unavailable": sum(report["status"] == "UNAVAILABLE" for report in reports),
            "operational_tickets": 0,
        },
        "claims": [
            "EXTERNAL REAL-DATA RESEARCH EVALUATION",
            "NO PUBLIC DATASET RESULT IS OSAT PLANT VALIDATION",
            "NO EXTERNAL BENCHMARK HAS OPERATIONAL OR TICKET AUTHORITY",
            "NO STEP-05 FAMILY MODEL IS FIT FROM EXTERNAL DATA",
        ],
    }


def real_data_summary(report: Mapping[str, Any]) -> dict[str, Any]:
    """Bound stdout to provenance, coverage, supported results, and limits."""

    if "datasets" in report:
        return {
            "version": report["version"],
            "origin": report["origin"],
            "summary": report["summary"],
            "datasets": [
                {
                    "dataset": item["dataset"],
                    "status": item["status"],
                    "evidence_class": item["evidence_class"],
                    "source_sha256": item["source_sha256"],
                    "channel_coverage": item["channel_coverage"],
                    "limitations": item["limitations"],
                }
                for item in report["datasets"]
            ],
            "claims": report["claims"],
        }
    keys = (
        "version",
        "dataset",
        "status",
        "source",
        "source_sha256",
        "origin",
        "evidence_class",
        "real_data",
        "mapped_channels",
        "channel_coverage",
        "full_station_representation",
        "split",
        "samples",
        "runs",
        "machines",
        "metrics_supported",
        "classification_metrics",
        "continuous_metrics",
        "state_distribution",
        "score_distribution",
        "unknown_fraction",
        "data_quality_coverage",
        "pipeline_coverage",
        "fault_evidence_records",
        "runtime",
        "operational_ticket_count",
        "limitations",
    )
    return {key: report[key] for key in keys if key in report}


def write_real_data_report(
    report: Mapping[str, Any],
    output_directory: str | Path = Path(".artifacts") / "real_data",
) -> Path:
    """Write the deterministic comparison filename only on explicit request."""

    root = Path(output_directory)
    root.mkdir(parents=True, exist_ok=True)
    path = root / "comparison.json"
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path
