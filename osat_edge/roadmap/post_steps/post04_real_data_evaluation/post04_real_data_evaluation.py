"""Isolated, offline evaluation of explicitly identified external real data.

This module may reuse Step 02 statistics and the pure Step 07 numerical scorer
where the source semantics make that defensible.  It never imports or calls
Steps 09, 10, or 15 and never attaches an external model to an operational
pipeline.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import importlib.metadata
import io
import json
import math
from pathlib import Path
import re
import tempfile
import time
from typing import Any, Mapping, Sequence
import zipfile
from xml.etree import ElementTree as ET

import numpy as np

from ..post03_external_benchmark.post03_external_benchmark import (
    BenchmarkError,
    NASA_OFFICIAL_ARCHIVE_SHA256,
    NASA_OFFICIAL_MAT_SHA256,
    analyze_nasa_milling,
)
from ...pre_steps.pre01_common.pre01_common import (
    ChannelSpec,
    DataOrigin,
    EquipmentState,
    MachineIdentity,
    OperatingContext,
    TelemetrySample,
    VERSION,
)
from ...pre_steps.pre02_machine_registry.pre02_machine_registry import StationDefinition
from ...pre_steps.pre03_data_provenance.pre03_data_provenance import (
    legacy_external_directory_hash as _directory_hash,
    md5_file as _md5_file,
    legacy_external_named_content_hash as _named_content_hash,
    sha256_file as _sha256_file,
)
from ...steps.step02_physical_features.step02_physical_features import (
    Feature,
    FeatureSet,
    extract_physical_features,
)
from ...steps.step07_machine_model.step07_machine_model import (
    ContextModel,
    MachineModel,
    evaluate_machine_model_numerically,
)
from ...steps.step08_live_telemetry.step08_live_telemetry import (
    BoundedTelemetryStore,
    TelemetryStatus,
    assess_telemetry,
)


DATASET_ORDER = (
    "st-awfd-d1",
    "st-awfd-d2",
    "tuhh-dad3350-surface",
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

POST04_ROOT = Path(__file__).resolve().parent
# This is the immutable historical 0.2.4 record, not a current-release artifact.
HISTORICAL_EVIDENCE_PATH = POST04_ROOT / "resources" / "0.2.4-real-data.json"
CURRENT_EVIDENCE_PATH = POST04_ROOT / "resources" / "0.2.5-real-data.json"
COMMITTED_EVIDENCE_PATH = CURRENT_EVIDENCE_PATH
DEFAULT_EXTERNAL_DATA_ROOT = (
    Path(__file__).resolve().parents[4] / "benchmarks" / "_external"
)

DATASETS: dict[str, dict[str, str]] = {
    "st-awfd-d1": {
        "title": "STMicroelectronics Automatic Wafer Fault Detection D1",
        "source": "https://github.com/STMicroelectronics/ST-AWFD",
        "evidence_class": "B",
        "domain": "semiconductor wafer-production process sequences",
    },
    "st-awfd-d2": {
        "title": "STMicroelectronics Automatic Wafer Fault Detection D2",
        "source": "https://github.com/STMicroelectronics/ST-AWFD",
        "evidence_class": "B",
        "domain": "semiconductor wafer-production process sequences",
    },
    "tuhh-dad3350-surface": {
        "title": "TUHH DISCO DAD3350 diced-surface profilometry",
        "source": "https://doi.org/10.15480/882.15763",
        "evidence_class": "A",
        "domain": "wafer-dicing surface metrology",
    },
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
MAXIMUM_KUKA_TOTAL_BYTES = 512 * 1024 * 1024
MAXIMUM_KUKA_ROWS_PER_FILE = 100_000
MAXIMUM_GENERIC_ARCHIVE_BYTES = 256 * 1024 * 1024
MAXIMUM_GENERIC_MEMBERS = 1_000
MAXIMUM_GENERIC_MEMBER_BYTES = 64 * 1024 * 1024
MAXIMUM_GENERIC_TOTAL_BYTES = 256 * 1024 * 1024

# Identities recorded from the authoritative versioned source artifacts used
# for the 0.2.4 release.  Schema compatibility alone never proves provenance.
KUKA_OFFICIAL_ARCHIVE_SHA256 = "51f93e8c453dd857170698627dc1d64ef14839e5c6efdb68148d01e0100c1253"
KUKA_OFFICIAL_ARCHIVE_MD5 = "efe9394bf2579f380832eed6d501c614"
KUKA_OFFICIAL_CSV_SET_SHA256 = "f3af97316d3366e0ac28f299025e36f4e9eeffc58e93c231f5a1c3b9ee4eeda4"
SECOM_OFFICIAL_ARCHIVE_SHA256 = "eea568baf3c2229096d7d294cf0b096b5502bd96d92c0b80a65b84714059be8e"
SECOM_OFFICIAL_FILE_SET_SHA256 = "29c8312b075821292d52eb8e3e20fbe6a4943272de3aa3900c6b9b19026dd927"
R2R_OFFICIAL_ARCHIVE_SHA256 = "3168a831e38c9388e73ba809661c282b560640ea269beba5d976340eb5e1ac16"
ST_AWFD_SOURCE_COMMIT = "54be5cc91b83615240710bda9745f51c984d10c5"
ST_AWFD_LICENSE = "CC BY-NC-SA 4.0"
ST_AWFD_SPECS: dict[str, dict[str, Any]] = {
    "st-awfd-d1": {
        "archive": "D1.zip",
        "member": "D1.csv",
        "sha256": "97b2df4206177c5bc5b89ba18758215674bd437fef8c514320b831404f7674b7",
        "feature_count": 15,
        "headline_steps": (2, 4, 5, 6, 7),
        "optional_steps": (-1, -2),
    },
    "st-awfd-d2": {
        "archive": "D2.zip",
        "member": "D2.csv",
        "sha256": "e93d9f69ecb5c303f7f484647406d1ac2beda5726b99bb2984801867fea36297",
        "feature_count": 20,
        "headline_steps": (1, 2),
        "optional_steps": (),
    },
}
ST_THRESHOLD_PROBES = {
    "WATCH_ENTRY": 0.35,
    "DEGRADED_ENTRY": 0.60,
    "CRITICAL_ENTRY": 0.82,
}
MAXIMUM_ST_ARCHIVE_BYTES = 32 * 1024 * 1024
MAXIMUM_ST_CSV_BYTES = 160 * 1024 * 1024

TUHH_DATA_ARCHIVE_SHA256 = "8dc6cd61c837100a0e5e9b7877e6b6c7e5bbde2f70e08017d48c4f0577125dca"
TUHH_DATA_ARCHIVE_MD5 = "e559d1736e23898b9d29e85b7f0ab3ed"
TUHH_README_SHA256 = "fdb9112d2061afef6b3af38647ef3ec10729983f9b159a978e7a5adc5d97715f"
TUHH_README_MD5 = "48d7f327a2d6068d8a130436762f1a20"
TUHH_FEED_FILES = {
    "data_raw/Dicing_surfaceroughness_white_light_0_1mms.vk7": 0.1,
    "data_raw/Dicing_surfaceroughness_white_light_0_2mms.vk7": 0.2,
    "data_raw/Dicing_surfaceroughness_white_light_0_5mms.vk7": 0.5,
    "data_raw/Dicing_surfaceroughness_white_light_0_7mms.vk7": 0.7,
    "data_raw/Dicing_surfaceroughness_white_light_1mms.vk7": 1.0,
    "data_raw/Dicing_surfaceroughness_white_light_5mms.vk7": 5.0,
}
KEYENCE_PARSER_DISTRIBUTION = "convert-keyence-files"
KEYENCE_PARSER_VERSION = "0.1.0"
KEYENCE_PARSER_COMMIT = "36e1eb9f550a41f5be2369de125ec51338f54d9e"
HISTORICAL_EVIDENCE_SHA256 = "371b9f6c40f2185a5d505f373483973f7f5974c276890d0616b9a715706014b3"
FORINFPRO_OFFICIAL_MD5 = {
    "cycle_001_machine_data.csv": "d2a7d96d133f3d7b43a5089ad4bf0b09",
    "cycle_001_pt.csv": "40d8511c11e8e0575dc3930ddd258c19",
    "cycle_001_us_rms.csv": "c767196cfd1b6dec0d09ed0a2dba2551",
}

R2R_METADATA_LABEL_FIELDS = frozenset({"Date", "Model", "Trigger", "Film kind"})
R2R_CONTROLLER_CONFIGURATION_PREFIXES = (
    "OutFeeder-Control:",
    "ReWinder-Control:",
)


class RealDataEvaluationError(ValueError):
    pass


class RealDataNotFound(RealDataEvaluationError):
    pass


def _bounded_directory_files(
    path: Path,
    *,
    maximum_members: int = MAXIMUM_GENERIC_MEMBERS,
    maximum_file_bytes: int = MAXIMUM_GENERIC_MEMBER_BYTES,
    maximum_total_bytes: int = MAXIMUM_GENERIC_TOTAL_BYTES,
) -> list[Path]:
    if not path.is_dir():
        raise RealDataEvaluationError("Expected a dataset directory")
    files: list[Path] = []
    total = 0
    for item in sorted(path.rglob("*")):
        if item.is_symlink():
            raise RealDataEvaluationError("Dataset directories may not contain symbolic links")
        if not item.is_file():
            continue
        files.append(item)
        if len(files) > maximum_members:
            raise RealDataEvaluationError("Dataset directory contains too many files")
        size = item.stat().st_size
        if size > maximum_file_bytes:
            raise RealDataEvaluationError("Dataset directory file exceeds the size limit")
        total += size
        if total > maximum_total_bytes:
            raise RealDataEvaluationError("Dataset directory exceeds the total size limit")
    return files


def _base_report(
    dataset_id: str,
    source_hash: str | None,
    *,
    provenance_verified: bool = False,
    provenance_method: str | None = None,
) -> dict[str, Any]:
    metadata = DATASETS[dataset_id]
    return {
        "version": VERSION,
        "dataset": dataset_id,
        "title": metadata["title"],
        "source": metadata["source"] if provenance_verified else None,
        "source_reference": metadata["source"],
        "source_sha256": source_hash,
        "origin": DataOrigin.EXTERNAL_BENCHMARK.value,
        "real_data": True if provenance_verified else None,
        "synthetic_data": False if provenance_verified else None,
        "provenance_verified": provenance_verified,
        "provenance_status": (
            "VERIFIED_OFFICIAL_ARTIFACT"
            if provenance_verified
            else "UNVERIFIED_OR_NOT_EVALUATED"
        ),
        "provenance_method": provenance_method,
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


def _rejected_invalid(dataset_id: str, source_hash: str | None, reason: str) -> dict[str, Any]:
    report = _base_report(dataset_id, source_hash)
    report.update(
        {
            "status": "REJECTED_INVALID",
            "mapped_channels": [],
            "channel_coverage": {"mapped": 0, "total": 0, "fraction": None},
            "full_station_representation": False,
            "limitations": [reason],
        }
    )
    return report


def _unverified_input(
    dataset_id: str,
    source_hash: str,
    reason: str,
    **observed: Any,
) -> dict[str, Any]:
    report = _base_report(dataset_id, source_hash)
    report.update(
        {
            "status": "UNVERIFIED_EXTERNAL_INPUT",
            "mapped_channels": [],
            "channel_coverage": {"mapped": 0, "total": 0, "fraction": None},
            "full_station_representation": False,
            "limitations": [reason],
            **observed,
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


def _fit_nominal_benchmark_model(
    identity: MachineIdentity,
    feature_sets: Sequence[FeatureSet],
) -> MachineModel:
    """Fit the unchanged Step 07 center/scale math to nominal benchmark runs.

    This deliberately does not construct Step 06 ``HealthyInterval`` or
    ``MachineHistory`` objects: the KUKA calibration runs are nominal workload
    data, not independently confirmed healthy equipment history.
    """

    if len(feature_sets) < 12:
        raise RealDataEvaluationError("Nominal benchmark baseline needs at least 12 runs")
    schema = set(feature_sets[0].by_name)
    for feature_set in feature_sets[1:]:
        schema.intersection_update(feature_set.by_name)
    names = tuple(name for name in feature_sets[0].by_name if name in schema)
    if not names:
        raise RealDataEvaluationError("Nominal benchmark runs share no usable features")
    matrix = np.asarray(
        [[row.by_name[name].value for name in names] for row in feature_sets],
        dtype=np.float64,
    )
    if not bool(np.isfinite(matrix).all()):
        raise RealDataEvaluationError("Nominal benchmark features must be finite")
    center = np.median(matrix, axis=0)
    mad = 1.4826 * np.median(np.abs(matrix - center), axis=0)
    standard = np.std(matrix, axis=0)
    floor = np.maximum(np.abs(center) * 1e-2, 1e-4)
    scale = np.where(mad > floor, mad, np.where(standard > floor, standard, floor))
    first = feature_sets[0].by_name
    context = ContextModel(
        equipment_state=EquipmentState.PROCESSING,
        feature_names=names,
        subsystems=tuple(first[name].subsystem for name in names),
        kinds=tuple(first[name].kind for name in names),
        center=np.asarray(center, dtype=np.float64),
        scale=np.asarray(scale, dtype=np.float64),
    )
    return MachineModel(
        machine=identity,
        origin=DataOrigin.EXTERNAL_BENCHMARK,
        contexts={EquipmentState.PROCESSING: context},
        physics_parameters={},
    )


def _binary_threshold_metrics(
    labels: Sequence[int], scores: Sequence[float], threshold: float
) -> dict[str, int | float | None]:
    truth = np.asarray(labels, dtype=np.int8)
    predicted = np.asarray(scores, dtype=np.float64) >= threshold
    positive = truth == 1
    negative = ~positive
    tp = int(np.sum(predicted & positive))
    fp = int(np.sum(predicted & negative))
    tn = int(np.sum(~predicted & negative))
    fn = int(np.sum(~predicted & positive))
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    specificity = tn / (tn + fp) if tn + fp else None
    f1 = (
        2.0 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and precision + recall
        else None
    )
    balanced_accuracy = (
        (recall + specificity) / 2.0
        if recall is not None and specificity is not None
        else None
    )
    denominator = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = (tp * tn - fp * fn) / denominator if denominator else None
    return {
        "threshold": threshold,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "balanced_accuracy": balanced_accuracy,
        "mcc": mcc,
    }


def _continuous_binary_metrics(
    labels: Sequence[int], scores: Sequence[float]
) -> dict[str, float | None]:
    truth = np.asarray(labels, dtype=np.int8)
    values = np.asarray(scores, dtype=np.float64)
    positives = int(np.sum(truth == 1))
    negatives = int(np.sum(truth == 0))
    if positives == 0 or negatives == 0:
        return {"auroc": None, "average_precision": None}
    ranks = _average_ranks(values)
    rank_sum = float(np.sum(ranks[truth == 1]))
    auroc = (rank_sum - positives * (positives - 1) / 2.0) / (
        positives * negatives
    )
    order = np.argsort(-values, kind="mergesort")
    sorted_scores = values[order]
    sorted_truth = truth[order]
    cumulative_positive = 0
    average_precision = 0.0
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and sorted_scores[end] == sorted_scores[start]:
            end += 1
        group_positive = int(np.sum(sorted_truth[start:end] == 1))
        cumulative_positive += group_positive
        average_precision += (
            group_positive / positives * cumulative_positive / end
        )
        start = end
    return {"auroc": float(auroc), "average_precision": average_precision}


def _score_distribution(values: Sequence[float]) -> dict[str, int | float | None]:
    if not values:
        return {
            "count": 0,
            "minimum": None,
            "median": None,
            "p95": None,
            "maximum": None,
        }
    array = np.asarray(values, dtype=np.float64)
    return {
        "count": len(array),
        "minimum": float(np.min(array)),
        "median": float(np.median(array)),
        "p95": float(np.percentile(array, 95.0)),
        "maximum": float(np.max(array)),
    }


def _st_identity(dataset_id: str, step_id: int) -> MachineIdentity:
    suffix = dataset_id.removeprefix("st-awfd-").upper()
    return MachineIdentity(
        machine_id=f"BENCH-{suffix}-STEP-{step_id}",
        family=f"external_{dataset_id.replace('-', '_')}",
        station_id=f"EXTERNAL-{suffix}-STEP-{step_id}",
        name=f"Anonymous ST-AWFD {suffix} StepID {step_id}",
    )


def _st_expected_header(feature_count: int) -> tuple[str, ...]:
    return (
        "MaterialID",
        "StepID",
        "duration_ms",
        *(f"feature_{index}" for index in range(1, feature_count + 1)),
        "is_test",
        "target",
    )


def _load_st_awfd_matrix(
    archive_path: Path, dataset_id: str
) -> tuple[tuple[str, ...], np.ndarray]:
    spec = ST_AWFD_SPECS[dataset_id]
    if archive_path.stat().st_size > MAXIMUM_ST_ARCHIVE_BYTES:
        raise RealDataEvaluationError("ST-AWFD archive exceeds the size limit")
    try:
        with zipfile.ZipFile(archive_path) as archive:
            files = [item for item in archive.infolist() if not item.is_dir()]
            if len(files) != 1 or files[0].filename != spec["member"]:
                raise RealDataEvaluationError(
                    f"{dataset_id} must contain only {spec['member']}"
                )
            item = files[0]
            if item.file_size > MAXIMUM_ST_CSV_BYTES:
                raise RealDataEvaluationError("ST-AWFD CSV exceeds the size limit")
            with archive.open(item) as stream:
                header = tuple(
                    value.strip()
                    for value in stream.readline().decode("utf-8-sig").split(",")
                )
                expected = _st_expected_header(spec["feature_count"])
                if header != expected:
                    raise RealDataEvaluationError(
                        f"{dataset_id} does not have the pinned official schema"
                    )
                try:
                    matrix = np.loadtxt(
                        stream,
                        delimiter=",",
                        dtype=np.float64,
                        ndmin=2,
                    )
                except (TypeError, ValueError) as exc:
                    raise RealDataEvaluationError(
                        f"{dataset_id} contains invalid or missing numeric data"
                    ) from exc
    except zipfile.BadZipFile as exc:
        raise RealDataEvaluationError("ST-AWFD archive is invalid") from exc
    if matrix.shape[1] != len(header):
        raise RealDataEvaluationError("ST-AWFD row width does not match its header")
    return header, matrix


def _validate_st_awfd_matrix(
    header: Sequence[str], matrix: np.ndarray
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    dict[int, tuple[int, int]],
]:
    columns = {name: index for index, name in enumerate(header)}
    material = matrix[:, columns["MaterialID"]]
    step = matrix[:, columns["StepID"]]
    duration = matrix[:, columns["duration_ms"]]
    split = matrix[:, columns["is_test"]]
    target = matrix[:, columns["target"]]
    feature_indexes = [
        columns[name] for name in header if name.startswith("feature_")
    ]
    features = matrix[:, feature_indexes]
    if not bool(np.isfinite(features).all()):
        raise RealDataEvaluationError(
            "ST-AWFD anonymous features contain nonfinite values; the source defines no missing-value sentinel"
        )
    if not bool(
        np.isfinite(material).all()
        and np.isfinite(step).all()
        and np.isfinite(duration).all()
        and np.isfinite(split).all()
        and np.isfinite(target).all()
    ):
        raise RealDataEvaluationError("ST-AWFD reference fields must be finite")
    for name, values in (
        ("MaterialID", material),
        ("StepID", step),
        ("is_test", split),
        ("target", target),
    ):
        if not bool(np.equal(values, np.floor(values)).all()):
            raise RealDataEvaluationError(f"ST-AWFD {name} must be integer-valued")
    if not set(np.unique(split)).issubset({0.0, 1.0}):
        raise RealDataEvaluationError("ST-AWFD is_test must contain only 0 or 1")
    if not set(np.unique(target)).issubset({0.0, 1.0}):
        raise RealDataEvaluationError("ST-AWFD target must contain only 0 or 1")
    material_int = material.astype(np.int64)
    step_int = step.astype(np.int64)
    split_int = split.astype(np.int8)
    target_int = target.astype(np.int8)
    unique_materials, inverse = np.unique(material_int, return_inverse=True)
    split_min = np.full(len(unique_materials), 2, dtype=np.int8)
    split_max = np.full(len(unique_materials), -1, dtype=np.int8)
    target_min = np.full(len(unique_materials), 2, dtype=np.int8)
    target_max = np.full(len(unique_materials), -1, dtype=np.int8)
    np.minimum.at(split_min, inverse, split_int)
    np.maximum.at(split_max, inverse, split_int)
    np.minimum.at(target_min, inverse, target_int)
    np.maximum.at(target_max, inverse, target_int)
    if not bool(np.equal(split_min, split_max).all()):
        raise RealDataEvaluationError("ST-AWFD is_test changes within a MaterialID")
    if not bool(np.equal(target_min, target_max).all()):
        raise RealDataEvaluationError("ST-AWFD target changes within a MaterialID")
    metadata = {
        int(material_id): (int(split_min[index]), int(target_min[index]))
        for index, material_id in enumerate(unique_materials)
    }
    return material_int, step_int, duration, features, target_int, metadata


def _st_feature_sets_for_step(
    dataset_id: str,
    step_id: int,
    material: np.ndarray,
    steps: np.ndarray,
    anonymous_features: np.ndarray,
    metadata: Mapping[int, tuple[int, int]],
) -> list[tuple[int, int, int, FeatureSet]]:
    selected = np.flatnonzero(steps == step_id)
    if len(selected) == 0:
        return []
    selected = selected[np.argsort(material[selected], kind="mergesort")]
    ordered_material = material[selected]
    boundaries = np.r_[
        0,
        np.flatnonzero(np.diff(ordered_material)) + 1,
        len(selected),
    ]
    identity = _st_identity(dataset_id, step_id)
    timestamp = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
    records: list[tuple[int, int, int, FeatureSet]] = []
    for start, end in zip(boundaries[:-1], boundaries[1:], strict=True):
        material_id = int(ordered_material[start])
        rows = anonymous_features[selected[start:end]]
        median = np.median(rows, axis=0)
        mad = np.median(np.abs(rows - median), axis=0)
        features: list[Any] = []
        for index, (location, spread) in enumerate(zip(median, mad, strict=True), 1):
            prefix = f"{dataset_id}.step_{step_id}.feature_{index}"
            subsystem = f"anonymous_process_step_{step_id}"
            features.append(Feature(prefix + ".median", float(location), subsystem, "location"))
            features.append(Feature(prefix + ".mad", float(spread), subsystem, "spread"))
        split, target = metadata[material_id]
        records.append(
            (
                material_id,
                split,
                target,
                FeatureSet(
                    identity,
                    timestamp,
                    EquipmentState.PROCESSING,
                    timestamp,
                    timestamp,
                    tuple(features),
                ),
            )
        )
    return records


def _evaluate_st_awfd(path: Path, dataset_id: str) -> dict[str, Any]:
    started = time.perf_counter()
    spec = ST_AWFD_SPECS[dataset_id]
    archive_path = path / spec["archive"] if path.is_dir() else path
    if not archive_path.is_file():
        raise RealDataNotFound(f"Official {spec['archive']} was not present")
    source_hash = _sha256_file(archive_path)
    if source_hash != spec["sha256"]:
        return _unverified_input(
            dataset_id,
            source_hash,
            "The ST-AWFD artifact does not match the pinned official GitHub archive SHA-256.",
            expected_official_archive_sha256=spec["sha256"],
        )
    header, matrix = _load_st_awfd_matrix(archive_path, dataset_id)
    material, steps, _duration, anonymous, _target_rows, metadata = (
        _validate_st_awfd_matrix(header, matrix)
    )
    training_materials = {
        material_id
        for material_id, (split, target) in metadata.items()
        if split == 0 and target == 0
    }
    held_out_materials = {
        material_id for material_id, (split, _target) in metadata.items() if split == 1
    }
    if training_materials & held_out_materials:
        raise RealDataEvaluationError("ST-AWFD MaterialID train/test leakage detected")
    all_scores: dict[int, list[float]] = {
        material_id: [] for material_id in held_out_materials
    }
    location_scores: dict[int, list[float]] = {
        material_id: [] for material_id in held_out_materials
    }
    step_results: list[dict[str, Any]] = []
    evaluated_feature_sets = 0
    for step_id in spec["headline_steps"]:
        records = _st_feature_sets_for_step(
            dataset_id, step_id, material, steps, anonymous, metadata
        )
        if not records:
            step_results.append(
                {
                    "step_id": step_id,
                    "status": "NO_SOURCE_ROWS",
                    "training_materials": 0,
                    "held_out_materials": 0,
                }
            )
            continue
        training = [
            feature_set
            for material_id, split, target, feature_set in records
            if material_id in training_materials and split == 0 and target == 0
        ]
        evaluation = [record for record in records if record[0] in held_out_materials]
        model = _fit_nominal_benchmark_model(_st_identity(dataset_id, step_id), training)
        available = 0
        for material_id, _split, _target, feature_set in evaluation:
            result = evaluate_machine_model_numerically(
                model, feature_set.machine, feature_set
            )
            evaluated_feature_sets += 1
            if not result.available:
                continue
            available += 1
            all_scores[material_id].append(
                max(deviation.score for deviation in result.deviations)
            )
            location_scores[material_id].append(
                max(
                    deviation.score
                    for deviation in result.deviations
                    if deviation.kind == "location"
                )
            )
        step_results.append(
            {
                "step_id": step_id,
                "status": "SCORED",
                "training_materials": len(training),
                "held_out_materials": len(evaluation),
                "available_scores": available,
            }
        )
    scored_materials = sorted(
        material_id for material_id, scores in location_scores.items() if scores
    )
    labels = [metadata[material_id][1] for material_id in scored_materials]
    location = [max(location_scores[material_id]) for material_id in scored_materials]
    maximum_all = [max(all_scores[material_id]) for material_id in scored_materials]
    normal = [score for score, label in zip(location, labels, strict=True) if label == 0]
    abnormal = [score for score, label in zip(location, labels, strict=True) if label == 1]
    unique_steps, step_counts = np.unique(steps, return_counts=True)
    step_row_coverage = {
        str(int(step_id)): int(count)
        for step_id, count in zip(unique_steps, step_counts, strict=True)
    }
    report = _base_report(
        dataset_id,
        source_hash,
        provenance_verified=True,
        provenance_method=(
            f"official STMicroelectronics GitHub commit {ST_AWFD_SOURCE_COMMIT}; "
            "pinned archive SHA-256"
        ),
    )
    report.update(
        {
            "status": "EXECUTED",
            "source_license": ST_AWFD_LICENSE,
            "source_commit": ST_AWFD_SOURCE_COMMIT,
            "source_schema": list(header),
            "mapped_channels": [],
            "channel_coverage": {
                "mapped": 0,
                "total": spec["feature_count"],
                "fraction": 0.0,
            },
            "source_field_coverage": {
                "anonymous_normalized_features_used": spec["feature_count"],
                "anonymous_normalized_features_available": spec["feature_count"],
                "fraction": 1.0,
            },
            "full_station_representation": False,
            "station_profile": None,
            "canonical_station_mapping": False,
            "machine_identity_available": False,
            "samples": int(len(matrix)),
            "runs": len(metadata),
            "machines": None,
            "split": "official MaterialID-level is_test split preserved",
            "training_materials": len(training_materials),
            "held_out_materials": len(held_out_materials),
            "held_out_label_counts": {
                "normal": int(sum(label == 0 for label in labels)),
                "abnormal": int(sum(label == 1 for label in labels)),
            },
            "headline_step_ids": list(spec["headline_steps"]),
            "optional_step_ids": list(spec["optional_steps"]),
            "step_row_coverage": step_row_coverage,
            "artifact_observations": (
                [
                    "The pinned D1 CSV has 602108 data rows and 5104 MaterialIDs; the repository README states 602108 rows and 5105 MaterialIDs.",
                    "The pinned D1 CSV contains StepID 1 and no StepID 5 although the repository README names StepID 5 as mandatory; neither identifier is relabeled.",
                ]
                if dataset_id == "st-awfd-d1"
                else [
                    "The pinned D2 CSV has 126794 data rows and 1156 MaterialIDs; the repository README states 126795 rows and 1157 MaterialIDs."
                ]
            ),
            "step_results": step_results,
            "feature_kinds_used": ["location", "spread"],
            "timing_dependent_features_used": False,
            "duration_ms_interpretation": (
                "normalized within-step process time only; no physical seconds or cross-MaterialID chronology"
            ),
            "nominal_baseline_semantics": (
                "is_test == 0 and target == 0 normal-process benchmark baseline; not independently confirmed healthy machine history"
            ),
            "method_scope": (
                "per-MaterialID/per-mandatory-StepID anonymous-feature median and MAD; frozen Step07 numerical deviation only"
            ),
            "pipeline": {
                "benchmark_feature_sets": True,
                "step01_physics": False,
                "step05_family_model": False,
                "step07_numerical_deviation": True,
                "step09_temporal_state_machine": False,
                "step10_evidence": False,
                "step15_ticket": False,
            },
            "step07_max_all_deviation_distribution": _score_distribution(maximum_all),
            "health_eligible_location_score_distribution": _score_distribution(location),
            "normal_location_score_distribution": _score_distribution(normal),
            "abnormal_location_score_distribution": _score_distribution(abnormal),
            "continuous_metrics": _continuous_binary_metrics(labels, location),
            "threshold_probes": {
                name: _binary_threshold_metrics(labels, location, threshold)
                for name, threshold in ST_THRESHOLD_PROBES.items()
            },
            "threshold_probe_semantics": (
                "static probes of frozen entry thresholds; these are not health states and no threshold was selected or optimized"
            ),
            "classification_metrics": None,
            "metrics_supported": [
                "held-out normal/abnormal continuous-score distributions",
                "AUROC and average precision",
                "frozen static-threshold confusion probes",
                "pipeline coverage",
            ],
            "data_quality_coverage": 1.0,
            "pipeline_coverage": (
                len(scored_materials) / len(held_out_materials)
                if held_out_materials
                else None
            ),
            "runtime": {
                "elapsed_seconds": time.perf_counter() - started,
                "evaluated_feature_sets": evaluated_feature_sets,
            },
            "operational_ticket_count": 0,
            "limitations": [
                "Real semiconductor production data with DataOrigin.EXTERNAL_BENCHMARK; not OSAT validation.",
                "The anonymous z-scaled feature semantics and physical engineering units are unavailable, so there is no Step01 physics or canonical station mapping.",
                "Actual machine IDs are unavailable; the benchmark model is not exact-machine validation.",
                "The normal-process calibration subset is not independently confirmed healthy machine history.",
                "duration_ms is normalized process-step time, so no slope or cross-MaterialID chronology is asserted.",
                "No Step05 family model, Step09 temporal state machine, Step10 evidence authority, or Step15 ticket authority is used.",
                "Labels describe abnormal MaterialIDs/process results, not confirmed equipment-maintenance faults.",
                *(
                    [
                        "The authoritative D1 bytes contain no StepID 5; the headline registry retains StepID 5 with NO_SOURCE_ROWS and does not substitute StepID 1."
                    ]
                    if dataset_id == "st-awfd-d1"
                    else []
                ),
            ],
        }
    )
    return report


def _keyence_parser() -> tuple[Any | None, dict[str, Any]]:
    try:
        distribution = importlib.metadata.distribution(KEYENCE_PARSER_DISTRIBUTION)
    except importlib.metadata.PackageNotFoundError:
        return None, {
            "status": "DEPENDENCY_UNAVAILABLE",
            "required_version": KEYENCE_PARSER_VERSION,
            "required_commit": KEYENCE_PARSER_COMMIT,
        }
    direct_text = distribution.read_text("direct_url.json")
    try:
        direct = json.loads(direct_text) if direct_text else {}
    except json.JSONDecodeError:
        direct = {}
    observed_commit = direct.get("vcs_info", {}).get("commit_id")
    if distribution.version != KEYENCE_PARSER_VERSION or observed_commit != KEYENCE_PARSER_COMMIT:
        return None, {
            "status": "PIN_MISMATCH",
            "observed_version": distribution.version,
            "observed_commit": observed_commit,
            "required_version": KEYENCE_PARSER_VERSION,
            "required_commit": KEYENCE_PARSER_COMMIT,
        }
    try:
        from convert_keyence_files import read
    except ImportError:
        return None, {"status": "IMPORT_FAILED"}
    return read, {
        "status": "AVAILABLE",
        "version": distribution.version,
        "commit": observed_commit,
        "license": "Unlicense",
    }


def _surface_statistics(height: Any) -> dict[str, Any]:
    array = np.asarray(height, dtype=np.float64)
    if array.ndim != 2 or min(array.shape) < 2 or array.size > 10_000_000:
        raise RealDataEvaluationError("Keyence height map dimensions exceed parser bounds")
    valid = np.isfinite(array)
    count = int(np.sum(valid))
    if count < 3:
        raise RealDataEvaluationError("Keyence height map has insufficient valid pixels")
    rows, columns = np.nonzero(valid)
    values = array[valid]
    x = columns.astype(np.float64)
    y = rows.astype(np.float64)
    design = np.asarray(
        [
            [np.dot(x, x), np.dot(x, y), np.sum(x)],
            [np.dot(x, y), np.dot(y, y), np.sum(y)],
            [np.sum(x), np.sum(y), count],
        ],
        dtype=np.float64,
    )
    response = np.asarray(
        [np.dot(x, values), np.dot(y, values), np.sum(values)],
        dtype=np.float64,
    )
    try:
        plane = np.linalg.solve(design, response)
    except np.linalg.LinAlgError as exc:
        raise RealDataEvaluationError("Keyence height map plane fit is singular") from exc
    residual = values - (plane[0] * x + plane[1] * y + plane[2])
    center = float(np.median(values))
    return {
        "dimensions": [int(array.shape[0]), int(array.shape[1])],
        "valid_pixel_fraction": count / int(array.size),
        "median_height": center,
        "robust_spread": float(np.median(np.abs(values - center))),
        "detrended_height_rms": float(np.sqrt(np.mean(np.square(residual)))),
        "detrended_mean_absolute_deviation": float(np.mean(np.abs(residual))),
        "peak_to_valley": float(np.max(values) - np.min(values)),
    }


def _evaluate_tuhh_surface(path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    if not path.is_dir():
        raise RealDataEvaluationError(
            "TUHH evaluation requires a directory containing data_raw.zip and README.txt"
        )
    archive_path = path / "data_raw.zip"
    readme_path = path / "README.txt"
    if not archive_path.is_file() or not readme_path.is_file():
        raise RealDataNotFound("Official TUHH data_raw.zip and README.txt were not both present")
    archive_sha = _sha256_file(archive_path)
    readme_sha = _sha256_file(readme_path)
    archive_md5 = _md5_file(archive_path)
    readme_md5 = _md5_file(readme_path)
    if (
        archive_sha != TUHH_DATA_ARCHIVE_SHA256
        or readme_sha != TUHH_README_SHA256
        or archive_md5 != TUHH_DATA_ARCHIVE_MD5
        or readme_md5 != TUHH_README_MD5
    ):
        return _unverified_input(
            "tuhh-dad3350-surface",
            archive_sha,
            "TUHH source files do not match the pinned authoritative v1.0 SHA-256/MD5 identities.",
            observed_readme_sha256=readme_sha,
        )
    try:
        with zipfile.ZipFile(archive_path) as archive:
            files = [item for item in archive.infolist() if not item.is_dir()]
            names = [item.filename for item in files]
            if len(names) != len(set(names)) or set(names) != set(TUHH_FEED_FILES):
                raise RealDataEvaluationError(
                    "TUHH archive must contain exactly the six pinned VK7 feed-velocity maps"
                )
            if any(
                Path(name).is_absolute() or ".." in Path(name).parts
                for name in names
            ):
                raise RealDataEvaluationError("TUHH archive contains an unsafe member path")
            if any(item.file_size > 8 * 1024 * 1024 for item in files):
                raise RealDataEvaluationError("TUHH VK7 member exceeds the parser bound")
            parser, parser_identity = _keyence_parser()
            if parser is None:
                report = _base_report(
                    "tuhh-dad3350-surface",
                    archive_sha,
                    provenance_verified=True,
                    provenance_method="pinned authoritative TORE v1.0 archive and README SHA-256/MD5",
                )
                report.update(
                    {
                        "status": "INSPECTED_NOT_EXECUTABLE",
                        "parser": parser_identity,
                        "mapped_channels": [],
                        "channel_coverage": {"mapped": 0, "total": 1, "fraction": 0.0},
                        "full_station_representation": False,
                        "limitations": [
                            "Pinned source identity and six-file schema verified, but the optional pinned parser is unavailable.",
                            "No descriptive height-map conversion was fabricated.",
                        ],
                    }
                )
                return report
            maps: list[dict[str, Any]] = []
            with tempfile.TemporaryDirectory() as directory:
                temporary = Path(directory)
                for item in sorted(files, key=lambda value: TUHH_FEED_FILES[value.filename]):
                    destination = temporary / Path(item.filename).name
                    destination.write_bytes(archive.read(item))
                    try:
                        parsed = parser(destination)
                        statistics = _surface_statistics(parsed.height)
                    except Exception as exc:
                        report = _base_report(
                            "tuhh-dad3350-surface",
                            archive_sha,
                            provenance_verified=True,
                            provenance_method="pinned authoritative TORE v1.0 archive and README SHA-256/MD5",
                        )
                        report.update(
                            {
                                "status": "INSPECTED_NOT_EXECUTABLE",
                                "parser": {**parser_identity, "status": "PARSER_FAILED"},
                                "mapped_channels": [],
                                "channel_coverage": {"mapped": 0, "total": 1, "fraction": 0.0},
                                "full_station_representation": False,
                                "limitations": [
                                    f"The pinned optional parser could not safely read all six official VK7 maps: {type(exc).__name__}.",
                                    "No converted values or fabricated substitute were used.",
                                ],
                            }
                        )
                        return report
                    maps.append(
                        {
                            "feed_velocity_mm_per_s": TUHH_FEED_FILES[item.filename],
                            **statistics,
                        }
                    )
    except zipfile.BadZipFile as exc:
        raise RealDataEvaluationError("TUHH data_raw.zip is invalid") from exc
    statistic_names = (
        "valid_pixel_fraction",
        "median_height",
        "robust_spread",
        "detrended_height_rms",
        "detrended_mean_absolute_deviation",
        "peak_to_valley",
    )
    feeds = [item["feed_velocity_mm_per_s"] for item in maps]
    associations = {
        name: _spearman(feeds, [item[name] for item in maps])
        for name in statistic_names
    }
    report = _base_report(
        "tuhh-dad3350-surface",
        archive_sha,
        provenance_verified=True,
        provenance_method="pinned authoritative TORE v1.0 archive and README SHA-256/MD5",
    )
    report.update(
        {
            "status": "EXECUTED_DESCRIPTIVE",
            "official_version": "v1.0",
            "source_license": "Public Domain Mark 1.0",
            "source_files": {
                "data_raw.zip": {"sha256": archive_sha, "md5": archive_md5},
                "README.txt": {"sha256": readme_sha, "md5": readme_md5},
            },
            "parser": parser_identity,
            "equipment": "DISCO DAD3350",
            "material": "fused-silica wafer, 1 mm thickness / 100 mm diameter",
            "spindle_speed_rpm": 30_000,
            "blade": "DISCO R07-SDC600-BB101-75",
            "mapped_channels": [],
            "channel_coverage": {"mapped": 0, "total": 1, "fraction": 0.0},
            "source_field_coverage": {
                "parsed_surface_maps": len(maps),
                "official_surface_maps": 6,
                "fraction": len(maps) / 6.0,
            },
            "full_station_representation": False,
            "samples": 6,
            "runs": 6,
            "machines": None,
            "feature_kinds_used": [],
            "timing_dependent_features_used": False,
            "metrics_supported": [
                "conservative per-map descriptive height statistics",
                "Spearman association with supplied feed velocity",
            ],
            "height_unit": "micrometre as decoded by the pinned parser",
            "surface_maps": maps,
            "feed_velocity_spearman": associations,
            "classification_metrics": None,
            "continuous_metrics": None,
            "method_scope": "descriptive target-process surface metrology only",
            "pipeline": {
                "step01_physics": False,
                "step05_family_model": False,
                "step07_machine_model": False,
                "step09_temporal_state_machine": False,
                "step10_evidence": False,
                "step15_ticket": False,
            },
            "data_quality_coverage": min(item["valid_pixel_fraction"] for item in maps),
            "pipeline_coverage": len(maps) / 6.0,
            "runtime": {"elapsed_seconds": time.perf_counter() - started},
            "operational_ticket_count": 0,
            "limitations": [
                "Real target-equipment/process evidence; not equipment-health validation and not OSAT evidence.",
                "Detrended metrics are descriptive proxies unless independently validated against Keyence VK-A3D output.",
                "No ISO surface-roughness compliance is claimed.",
                "One surface map per feed velocity supports descriptive rank association only, not causal inference.",
                "Steps 07, 09, 10, and 15 are not run and no operational ticket authority exists.",
            ],
        }
    )
    return report


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


def _zip_members(path: Path) -> tuple[str, str, dict[str, bytes]]:
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
                if len({item.filename for item in files}) != len(files):
                    raise RealDataEvaluationError("Dataset ZIP contains duplicate member names")
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
        return _sha256_file(selected), _named_content_hash(list(members.items())), members
    if path.is_dir():
        files = _bounded_directory_files(path)
        members = {item.relative_to(path).as_posix(): item.read_bytes() for item in files}
        return _directory_hash(path, files), _named_content_hash(list(members.items())), members
    if path.stat().st_size > MAXIMUM_GENERIC_MEMBER_BYTES:
        raise RealDataEvaluationError("Dataset file exceeds the size limit")
    content = path.read_bytes()
    members = {path.name: content}
    return _sha256_file(path), _named_content_hash(list(members.items())), members


def _evaluate_secom(path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    source_hash, content_hash, members = _zip_members(path)
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
    verified = (
        source_hash == SECOM_OFFICIAL_ARCHIVE_SHA256
        or content_hash == SECOM_OFFICIAL_FILE_SET_SHA256
    )
    if not verified:
        return _unverified_input(
            "uci-secom",
            source_hash,
            "The files are SECOM-compatible, but neither the source archive nor canonical file-set hash matches the pinned official dataset.",
            samples=len(data_lines),
            observed_variable_count=next(iter(widths)),
            observed_label_counts={"pass": labels.count(-1), "fail": labels.count(1)},
            canonical_content_sha256=content_hash,
        )
    report = _base_report(
        "uci-secom",
        source_hash,
        provenance_verified=True,
        provenance_method=(
            "pinned official archive SHA-256"
            if source_hash == SECOM_OFFICIAL_ARCHIVE_SHA256
            else "pinned canonical official file-set SHA-256"
        ),
    )
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


def _xlsx_first_row(content: bytes) -> tuple[str, ...]:
    namespace = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as workbook:
            files = [item for item in workbook.infolist() if not item.is_dir()]
            if len(files) > MAXIMUM_GENERIC_MEMBERS:
                raise RealDataEvaluationError("XLSX contains too many members")
            if any(item.file_size > MAXIMUM_GENERIC_MEMBER_BYTES for item in files):
                raise RealDataEvaluationError("XLSX member exceeds the size limit")
            if sum(item.file_size for item in files) > MAXIMUM_GENERIC_TOTAL_BYTES:
                raise RealDataEvaluationError("XLSX expands beyond the size limit")

            shared: list[str] = []
            if "xl/sharedStrings.xml" in workbook.namelist():
                shared_root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
                for item in shared_root.findall(f"{{{namespace}}}si"):
                    shared.append(
                        "".join(node.text or "" for node in item.iter(f"{{{namespace}}}t"))
                    )
            sheet = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        raise RealDataEvaluationError("R2R workbook is invalid or lacks sheet1") from exc
    first_row = sheet.find(f".//{{{namespace}}}sheetData/{{{namespace}}}row")
    if first_row is None:
        raise RealDataEvaluationError("R2R workbook has no header row")
    values: list[str] = []
    for cell in first_row.findall(f"{{{namespace}}}c"):
        cell_type = cell.get("t")
        raw = cell.find(f"{{{namespace}}}v")
        value = "" if raw is None else raw.text or ""
        if cell_type == "s" and value:
            try:
                value = shared[int(value)]
            except (IndexError, ValueError) as exc:
                raise RealDataEvaluationError("R2R workbook has an invalid shared string") from exc
        elif cell_type == "inlineStr":
            value = "".join(
                node.text or "" for node in cell.iter(f"{{{namespace}}}t")
            )
        if value.strip():
            values.append(value.strip())
    return tuple(values)


def _classify_r2r_source_fields(
    fields: Sequence[str],
) -> dict[str, tuple[str, ...]]:
    """Classify the pinned v2 sensor schema without counting metadata as signals.

    Date/model/trigger/material labels are metadata.  Named controller tuning
    fields are configuration.  Every other field in the checksum-pinned sensor
    schema is a physical-valued source field, whether or not Fleet Command has
    an exact canonical mapping for it.
    """

    classified: dict[str, list[str]] = {
        "physical_signal": [],
        "metadata_or_label": [],
        "controller_configuration": [],
    }
    for field in fields:
        if field in R2R_METADATA_LABEL_FIELDS:
            classified["metadata_or_label"].append(field)
        elif field.startswith(R2R_CONTROLLER_CONFIGURATION_PREFIXES):
            classified["controller_configuration"].append(field)
        else:
            classified["physical_signal"].append(field)
    return {name: tuple(values) for name, values in classified.items()}


def _r2r_source_field_coverage(
    fields: Sequence[str], mapped_sources: set[str]
) -> tuple[dict[str, Any], dict[str, Any]]:
    classified = _classify_r2r_source_fields(fields)
    physical_fields = classified["physical_signal"]
    if not mapped_sources.issubset(physical_fields):
        raise RealDataEvaluationError("R2R mapped fields must classify as physical source signals")
    mapped_count = len(mapped_sources)
    physical_count = len(physical_fields)
    if physical_count == 0:
        raise RealDataEvaluationError("R2R source schema has no physical signal fields")
    fraction = mapped_count / physical_count
    return (
        {"mapped": mapped_count, "total": physical_count, "fraction": fraction},
        {
            "exact_mapped_physical_signals": mapped_count,
            "physical_signal_fields": physical_count,
            "inspected_source_fields": len(fields),
            "metadata_or_label_fields_excluded": len(classified["metadata_or_label"]),
            "controller_configuration_fields_excluded": len(
                classified["controller_configuration"]
            ),
            "fraction": fraction,
            "classification_rule": (
                "For the checksum-pinned v2 sensor schema, Date/Model/Trigger/Film kind "
                "are metadata or labels; OutFeeder-Control:/ReWinder-Control: fields are "
                "controller configuration; all remaining physical-valued fields form "
                "the source-signal denominator."
            ),
        },
    )


def _evaluate_r2r(path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    source_hash, _content_hash, members = _zip_members(path)
    if source_hash != R2R_OFFICIAL_ARCHIVE_SHA256:
        return _unverified_input(
            "r2r-web-tension",
            source_hash,
            "The local artifact does not match the pinned public Mendeley Data v2 dataset.zip SHA-256.",
            files=len(members),
            expected_official_archive_sha256=R2R_OFFICIAL_ARCHIVE_SHA256,
        )
    aggregate = [
        content
        for name, content in members.items()
        if name.replace("\\", "/").endswith("dataset/dataset.xlsx")
    ]
    sensor_items = [
        (name, content)
        for name, content in members.items()
        if "/sensor_data/" in name.replace("\\", "/") and name.lower().endswith(".xlsx")
    ]
    if len(aggregate) != 1 or not sensor_items:
        raise RealDataEvaluationError("Official R2R archive lacks its aggregate or sensor workbooks")
    aggregate_header = _xlsx_first_row(aggregate[0])
    sensor_headers = {_xlsx_first_row(content) for _name, content in sensor_items}
    if len(sensor_headers) != 1:
        raise RealDataEvaluationError("R2R sensor workbooks do not share one source schema")
    sensor_header = next(iter(sensor_headers))
    mapped = (
        ("Film Tension #1 (kg)", "film_tension_1", "kg"),
        ("Film Tension #2 (kg)", "film_tension_2", "kg"),
        ("Film Tension #3 (kg)", "film_tension_3", "kg"),
        ("Web Current Speed (mm/sec)", "web_speed", "mm/sec"),
    )
    missing = sorted(source for source, _target, _unit in mapped if source not in sensor_header)
    if missing:
        raise RealDataEvaluationError(
            f"R2R exact physical source fields are missing: {', '.join(missing)}"
        )
    mapped_sources = {source for source, _target, _unit in mapped}
    channel_coverage, source_field_coverage = _r2r_source_field_coverage(
        sensor_header, mapped_sources
    )
    report = _base_report(
        "r2r-web-tension",
        source_hash,
        provenance_verified=True,
        provenance_method="pinned public Mendeley Data v2 dataset.zip SHA-256",
    )
    report.update(
        {
            "status": "INSPECTED_NOT_EXECUTABLE",
            "official_version": "2",
            "mapped_channels": [
                {
                    "source": source,
                    "benchmark_channel": target,
                    "unit": unit,
                    "subsystem": "web_transport",
                }
                for source, target, unit in mapped
            ],
            "channel_coverage": channel_coverage,
            "source_field_coverage": source_field_coverage,
            "full_station_representation": False,
            "runs": len(sensor_items),
            "samples": None,
            "machines": None,
            "aggregate_fields": len(aggregate_header),
            "sensor_fields": len(sensor_header),
            "classification_metrics": None,
            "runtime": {"elapsed_seconds": time.perf_counter() - started},
            "limitations": [
                "Evidence class C roll-to-roll mechanism analog; not semiconductor or OSAT validation.",
                "Four of 20 classified physical-valued source fields have exact Fleet Command mappings; selected-field coverage is not reported as 100% channel coverage.",
                "The four mapped fields have explicit physical semantics and units, but the dataset provides process-setting experiments rather than equipment-health labels.",
                "No confirmed-healthy exact-machine history or preregistered health split exists, so no Step 07/09/10 result is produced.",
                "The workbooks are schema-inspected only; controller settings, material geometry, and derived aggregate columns are not PHM channels.",
            ],
        }
    )
    return report


def _evaluate_forinfpro(path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    if path.is_dir():
        bounded = _bounded_directory_files(path)
        files = [item for item in bounded if item.suffix.lower() == ".csv"]
    else:
        if path.stat().st_size > MAXIMUM_GENERIC_MEMBER_BYTES:
            raise RealDataEvaluationError("FORinFPRO file exceeds the size limit")
        files = [path]
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
    source_hash = _directory_hash(path, files) if path.is_dir() else _sha256_file(path)
    observed_md5 = {item.name: _md5_file(item) for item in files}
    verified = observed_md5 == FORINFPRO_OFFICIAL_MD5
    if not verified:
        return _unverified_input(
            "forinfpro-himd",
            source_hash,
            "The local files do not match the complete three-file MD5 manifest for official FORinFPRO-HIMD v1.",
            files=schemas,
            observed_file_md5=observed_md5,
            expected_official_file_md5=FORINFPRO_OFFICIAL_MD5,
        )
    report = _base_report(
        "forinfpro-himd",
        source_hash,
        provenance_verified=True,
        provenance_method="complete official v1 three-file MD5 manifest",
    )
    report.update(
        {
            "status": "INSPECTED_NOT_EXECUTABLE",
            "official_version": "v1",
            "official_file_md5": observed_md5,
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
    verified = (
        source["source_artifact_sha256"] == NASA_OFFICIAL_ARCHIVE_SHA256
        or source["mill_mat_sha256"] == NASA_OFFICIAL_MAT_SHA256
    )
    if not verified:
        return _unverified_input(
            "nasa-milling",
            source["source_artifact_sha256"],
            "The input is structurally compatible with NASA Milling, but neither its source artifact nor canonical mill.mat hash matches the pinned official dataset.",
            observed_runs=source["runs"],
            canonical_mat_sha256=source["mill_mat_sha256"],
        )
    report = _base_report(
        "nasa-milling",
        source["source_artifact_sha256"],
        provenance_verified=True,
        provenance_method=(
            "pinned official archive SHA-256"
            if source["source_artifact_sha256"] == NASA_OFFICIAL_ARCHIVE_SHA256
            else "pinned canonical official mill.mat SHA-256"
        ),
    )
    report.update(
        {
            "status": "EXECUTED_DESCRIPTIVE",
            "canonical_mat_sha256": source["mill_mat_sha256"],
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
    if path.is_file():
        if path.stat().st_size > MAXIMUM_GENERIC_ARCHIVE_BYTES:
            raise RealDataEvaluationError("Dataset artifact exceeds the inspection size limit")
        files = [path]
    else:
        files = _bounded_directory_files(path)
    if not files:
        raise RealDataNotFound("No local dataset artifact was present.")
    source_hash = _sha256_file(path) if path.is_file() else _directory_hash(path, files)
    return _unverified_input(
        dataset_id,
        source_hash,
        "No pinned official artifact or canonical-content identity is registered for this dataset; local bytes cannot be declared verified real data.",
        files=len(files),
    )


def evaluate_real_dataset(dataset_id: str, path: str | Path) -> dict[str, Any]:
    """Evaluate one explicit local external dataset without operational authority."""

    if dataset_id not in DATASETS:
        raise RealDataEvaluationError(f"Unknown external dataset {dataset_id!r}")
    selected = Path(path)
    if not selected.exists():
        raise RealDataNotFound(f"Dataset path not found: {selected.name}")
    if dataset_id in ST_AWFD_SPECS:
        return _evaluate_st_awfd(selected, dataset_id)
    if dataset_id == "tuhh-dad3350-surface":
        return _evaluate_tuhh_surface(selected)
    if dataset_id == "kuka-kr3":
        return _evaluate_kuka(selected)
    if dataset_id == "nasa-milling":
        return _evaluate_nasa(selected)
    if dataset_id == "uci-secom":
        return _evaluate_secom(selected)
    if dataset_id == "forinfpro-himd":
        return _evaluate_forinfpro(selected)
    if dataset_id == "r2r-web-tension":
        return _evaluate_r2r(selected)
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
        except RealDataNotFound as exc:
            reports.append(_unavailable(dataset_id, str(exc)))
        except RealDataEvaluationError as exc:
            reports.append(_rejected_invalid(dataset_id, None, str(exc)))
    return {
        "version": VERSION,
        "origin": DataOrigin.EXTERNAL_BENCHMARK.value,
        "dataset_order": list(DATASET_ORDER),
        "datasets": reports,
        "summary": {
            "attempted": len(reports),
            "executed": sum(report["status"].startswith("EXECUTED") for report in reports),
            "inspected_not_executable": sum(report["status"] == "INSPECTED_NOT_EXECUTABLE" for report in reports),
            "unverified_external_input": sum(report["status"] == "UNVERIFIED_EXTERNAL_INPUT" for report in reports),
            "rejected_invalid": sum(report["status"] == "REJECTED_INVALID" for report in reports),
            "unavailable": sum(report["status"] == "UNAVAILABLE" for report in reports),
            "operational_tickets": 0,
        },
        "claims": [
            "EXTERNAL-DATA RESEARCH EVALUATION; REAL-DATA STATUS REQUIRES PINNED PROVENANCE",
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
                    "real_data": item["real_data"],
                    "provenance_verified": item["provenance_verified"],
                    "source_sha256": item["source_sha256"],
                    "channel_coverage": item["channel_coverage"],
                    "source_field_coverage": item.get("source_field_coverage"),
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
        "source_reference",
        "source_sha256",
        "origin",
        "evidence_class",
        "real_data",
        "synthetic_data",
        "provenance_verified",
        "provenance_status",
        "provenance_method",
        "mapped_channels",
        "channel_coverage",
        "source_field_coverage",
        "full_station_representation",
        "split",
        "samples",
        "runs",
        "machines",
        "metrics_supported",
        "classification_metrics",
        "continuous_metrics",
        "threshold_probes",
        "threshold_probe_semantics",
        "method_scope",
        "feature_kinds_used",
        "timing_dependent_features_used",
        "nominal_baseline_semantics",
        "deviation_score_distribution",
        "step07_max_all_deviation_distribution",
        "health_eligible_location_score_distribution",
        "normal_location_score_distribution",
        "abnormal_location_score_distribution",
        "headline_step_ids",
        "optional_step_ids",
        "step_row_coverage",
        "artifact_observations",
        "surface_maps",
        "feed_velocity_spearman",
        "parser",
        "data_quality_coverage",
        "pipeline_coverage",
        "runtime",
        "operational_ticket_count",
        "limitations",
    )
    return {key: report[key] for key in keys if key in report}


def deterministic_scientific_report(value: Any) -> Any:
    """Remove machine-dependent timings from the reproducible report artifact."""

    if isinstance(value, Mapping):
        return {
            key: deterministic_scientific_report(item)
            for key, item in value.items()
            if key != "runtime"
        }
    if isinstance(value, (list, tuple)):
        return [deterministic_scientific_report(item) for item in value]
    return value


def deterministic_scientific_bytes(report: Mapping[str, Any]) -> bytes:
    """Serialize scientific results without machine-dependent runtime fields."""

    return (
        json.dumps(
            deterministic_scientific_report(report),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")


def deterministic_scientific_sha256(report: Mapping[str, Any]) -> str:
    return hashlib.sha256(deterministic_scientific_bytes(report)).hexdigest()


def verify_historical_real_data_artifact(
    historical_result: str | Path | None = None,
) -> dict[str, Any]:
    """Verify the immutable 0.2.4 bytes without reproducing them as 0.2.5."""

    path = Path(historical_result) if historical_result else HISTORICAL_EVIDENCE_PATH
    try:
        observed_hash = _sha256_file(path)
        stored = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RealDataEvaluationError(
            f"Historical real-data evidence is unavailable or invalid: {path.name}"
        ) from exc
    if observed_hash != HISTORICAL_EVIDENCE_SHA256:
        raise RealDataEvaluationError(
            "HISTORICAL 0.2.4 ARTIFACT INTEGRITY FAILURE: byte identity changed"
        )
    if stored.get("release_version") != "0.2.4" or stored.get("schema_version") != "1.0":
        raise RealDataEvaluationError(
            "HISTORICAL 0.2.4 ARTIFACT INTEGRITY FAILURE: embedded identity changed"
        )
    return {
        "status": "PASS",
        "artifact": path.name,
        "release_version": "0.2.4",
        "artifact_sha256": observed_hash,
        "meaning": "historical artifact integrity only; not current scientific reproduction",
    }


def current_real_data_evidence_record(report: Mapping[str, Any]) -> dict[str, Any]:
    """Return the small 0.2.5 evidence record; never include sample-level data."""

    result_keys = (
        "dataset",
        "status",
        "source_sha256",
        "source_license",
        "source_commit",
        "source_files",
        "provenance_status",
        "provenance_method",
        "samples",
        "runs",
        "machines",
        "split",
        "training_materials",
        "held_out_materials",
        "held_out_label_counts",
        "headline_step_ids",
        "optional_step_ids",
        "step_row_coverage",
        "artifact_observations",
        "step_results",
        "method_scope",
        "pipeline",
        "step07_max_all_deviation_distribution",
        "health_eligible_location_score_distribution",
        "normal_location_score_distribution",
        "abnormal_location_score_distribution",
        "continuous_metrics",
        "threshold_probes",
        "threshold_probe_semantics",
        "source_field_coverage",
        "surface_maps",
        "feed_velocity_spearman",
        "data_quality_coverage",
        "pipeline_coverage",
        "operational_ticket_count",
        "limitations",
    )
    results = [
        {key: item[key] for key in result_keys if key in item}
        for item in report["datasets"]
    ]
    return {
        "schema_version": "1.0",
        "release_version": VERSION,
        "origin": DataOrigin.EXTERNAL_BENCHMARK.value,
        "historical_artifact": {
            "name": HISTORICAL_EVIDENCE_PATH.name,
            "sha256": HISTORICAL_EVIDENCE_SHA256,
            "reproduced_as_current": False,
        },
        "evaluator_sha256": _sha256_file(Path(__file__).resolve()),
        "deterministic_comparison_report_sha256": deterministic_scientific_sha256(report),
        "methodology": {
            "threshold_selection": "none; frozen threshold probes only",
            "step05_family_model": False,
            "step09_temporal_state_machine": False,
            "operational_ticket_authority": False,
            "sample_level_data_committed": False,
        },
        "summary": report["summary"],
        "results": results,
    }


def write_current_real_data_evidence(
    report: Mapping[str, Any],
    output_path: str | Path = CURRENT_EVIDENCE_PATH,
) -> Path:
    """Write the deterministic aggregate-only current evidence record."""

    path = Path(output_path)
    path.write_bytes(deterministic_scientific_bytes(current_real_data_evidence_record(report)))
    return path


def verify_committed_real_data_evidence(
    external_root: str | Path,
    committed_result: str | Path | None = None,
) -> dict[str, Any]:
    """Regenerate current evidence separately from historical-artifact integrity.

    This path performs no download.  The caller must provide the ignored local
    dataset root used for the committed evidence record.
    """

    historical = (
        verify_historical_real_data_artifact()
        if committed_result is None
        else None
    )
    expected_path = Path(committed_result) if committed_result else CURRENT_EVIDENCE_PATH
    try:
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RealDataEvaluationError(
            f"Committed real-data evidence is unavailable or invalid: {expected_path.name}"
        ) from exc
    evaluator_hash = _sha256_file(Path(__file__).resolve())
    regenerated = evaluate_all_real_data(external_root)
    report_hash = deterministic_scientific_sha256(regenerated)
    drift: list[str] = []
    if expected.get("release_version") != VERSION:
        drift.append("release version")
    if expected.get("evaluator_sha256") != evaluator_hash:
        drift.append("evaluator SHA-256")
    if expected.get("deterministic_comparison_report_sha256") != report_hash:
        drift.append("deterministic comparison report SHA-256")
    if expected.get("summary") != regenerated.get("summary"):
        drift.append("summary")
    regenerated_by_id = {item["dataset"]: item for item in regenerated["datasets"]}
    for item in expected.get("results", []):
        current = regenerated_by_id.get(item.get("dataset"))
        if current is None:
            drift.append(f"missing dataset {item.get('dataset')}")
            continue
        for field in ("status", "source_sha256", "channel_coverage"):
            if field in item and item[field] != current.get(field):
                drift.append(f"{item['dataset']} {field}")
    if drift:
        raise RealDataEvaluationError(
            "CURRENT SCIENTIFIC REPRODUCTION DRIFT: " + ", ".join(drift)
        )
    result = {
        "status": "PASS",
        "release_version": VERSION,
        "evaluator_sha256": evaluator_hash,
        "deterministic_comparison_report_sha256": report_hash,
        "datasets_checked": len(expected.get("results", [])),
        "operational_tickets": regenerated["summary"]["operational_tickets"],
    }
    if historical is not None:
        result["historical_artifact_integrity"] = historical
    return result


def write_real_data_report(
    report: Mapping[str, Any],
    output_directory: str | Path = Path(".artifacts") / "real_data",
) -> Path:
    """Write the deterministic comparison filename only on explicit request."""

    root = Path(output_directory)
    root.mkdir(parents=True, exist_ok=True)
    path = root / "comparison.json"
    path.write_bytes(deterministic_scientific_bytes(report))
    return path
