"""Isolated descriptive analysis of the external NASA Milling data set."""

from __future__ import annotations

import hashlib
import io
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import zipfile

import numpy as np

from .common import DataOrigin, VERSION


NASA_DATASET_TITLE = "NASA/UC Berkeley Milling Data Set"
NASA_REPOSITORY_URL = (
    "https://www.nasa.gov/intelligent-systems-division/"
    "discovery-and-systems-health/pcoe/pcoe-data-set-repository/"
)
NASA_OPEN_DATA_URL = "https://data.nasa.gov/dataset/milling-wear"
NASA_OFFICIAL_ARCHIVE_SHA256 = "de9c8685cb0e07b4f39459dc282b49192a3ad660e9577ff99b68dc9994e35d27"
NASA_OFFICIAL_MAT_SHA256 = "71486a857939d1416c86c7cf0c469d5e69c7c30495e01ec8a0e13aafd2a313cb"
REQUIRED_FIELDS = (
    "case",
    "run",
    "VB",
    "time",
    "DOC",
    "feed",
    "material",
    "smcAC",
    "smcDC",
    "vib_table",
    "vib_spindle",
    "AE_table",
    "AE_spindle",
)
ANALYZED_SIGNALS = ("smcAC", "smcDC", "vib_spindle")
MAXIMUM_MAT_BYTES = 128 * 1024 * 1024
MAXIMUM_SOURCE_ARTIFACT_BYTES = 256 * 1024 * 1024
MAXIMUM_ARCHIVE_MEMBERS = 100
MAXIMUM_ARCHIVE_NESTING = 1
MAXIMUM_RECORDS = 10_000
MAXIMUM_SIGNAL_SAMPLES = 1_000_000
MAXIMUM_TOTAL_ANALYZED_SIGNAL_SAMPLES = 20_000_000


class BenchmarkError(ValueError):
    pass


class BenchmarkDatasetNotFound(BenchmarkError):
    pass


class BenchmarkDependencyError(BenchmarkError):
    pass


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _single_member(archive: zipfile.ZipFile, suffix: str) -> zipfile.ZipInfo | None:
    matches = [item for item in archive.infolist() if item.filename.lower().endswith(suffix)]
    if len(matches) > 1:
        raise BenchmarkError(f"Dataset archive contains multiple {suffix} files")
    return matches[0] if matches else None


def _validate_archive(archive: zipfile.ZipFile, *, nesting: int) -> None:
    if nesting > MAXIMUM_ARCHIVE_NESTING:
        raise BenchmarkError("Dataset archive nesting exceeds the analysis limit")
    if len(archive.infolist()) > MAXIMUM_ARCHIVE_MEMBERS:
        raise BenchmarkError("Dataset archive contains too many members")


def _member_bytes(archive: zipfile.ZipFile, member: zipfile.ZipInfo) -> bytes:
    if member.file_size > MAXIMUM_MAT_BYTES:
        raise BenchmarkError("Dataset archive member exceeds the analysis size limit")
    with archive.open(member) as stream:
        value = stream.read(MAXIMUM_MAT_BYTES + 1)
    if len(value) > MAXIMUM_MAT_BYTES:
        raise BenchmarkError("Dataset archive member exceeds the analysis size limit")
    if len(value) != member.file_size:
        raise BenchmarkError("Dataset archive member size does not match its metadata")
    return value


def _mat_source(path: Path) -> tuple[str | io.BytesIO, str, str, str, str]:
    if not path.exists():
        raise BenchmarkDatasetNotFound("NASA MILLING DATASET NOT FOUND")
    if path.is_dir():
        files: list[Path] = []
        total = 0
        for item in sorted(path.rglob("*")):
            if item.is_symlink():
                raise BenchmarkError("Dataset directories may not contain symbolic links")
            if not item.is_file():
                continue
            files.append(item)
            if len(files) > MAXIMUM_ARCHIVE_MEMBERS:
                raise BenchmarkError("Dataset directory contains too many files")
            size = item.stat().st_size
            if size > MAXIMUM_SOURCE_ARTIFACT_BYTES:
                raise BenchmarkError("Dataset directory file exceeds the analysis size limit")
            total += size
            if total > MAXIMUM_SOURCE_ARTIFACT_BYTES:
                raise BenchmarkError("Dataset directory exceeds the total analysis size limit")
        matches = [item for item in files if item.name.casefold() == "mill.mat"]
        if len(matches) != 1:
            raise BenchmarkError("Dataset directory must contain exactly one mill.mat")
        selected = matches[0]
        if selected.stat().st_size > MAXIMUM_MAT_BYTES:
            raise BenchmarkError("MATLAB dataset exceeds the analysis size limit")
        mill_hash = _sha256_file(selected)
        return (
            str(selected),
            mill_hash,
            mill_hash,
            path.name or ".",
            selected.relative_to(path).as_posix(),
        )
    if path.suffix.lower() == ".mat":
        if path.stat().st_size > MAXIMUM_MAT_BYTES:
            raise BenchmarkError("MATLAB dataset exceeds the analysis size limit")
        mill_hash = _sha256_file(path)
        return str(path), mill_hash, mill_hash, path.name, path.name
    if path.suffix.lower() != ".zip":
        raise BenchmarkError("Dataset path must be mill.mat, an extracted directory, or a ZIP")
    if path.stat().st_size > MAXIMUM_SOURCE_ARTIFACT_BYTES:
        raise BenchmarkError("Dataset source artifact exceeds the analysis size limit")
    package_hash = _sha256_file(path)
    try:
        with zipfile.ZipFile(path) as outer:
            _validate_archive(outer, nesting=0)
            mat = _single_member(outer, ".mat")
            if mat is not None:
                value = _member_bytes(outer, mat)
                return (
                    io.BytesIO(value),
                    _sha256_bytes(value),
                    package_hash,
                    path.name,
                    f"{path.name}!{mat.filename}",
                )
            nested = _single_member(outer, ".zip")
            if nested is None:
                raise BenchmarkError("Dataset ZIP contains no mill.mat or nested ZIP")
            nested_value = _member_bytes(outer, nested)
        with zipfile.ZipFile(io.BytesIO(nested_value)) as inner:
            _validate_archive(inner, nesting=1)
            mat = _single_member(inner, ".mat")
            if mat is None:
                if _single_member(inner, ".zip") is not None:
                    raise BenchmarkError(
                        "Dataset archive nesting exceeds the analysis limit"
                    )
                raise BenchmarkError("Nested dataset ZIP contains no mill.mat")
            value = _member_bytes(inner, mat)
            return (
                io.BytesIO(value),
                _sha256_bytes(value),
                package_hash,
                path.name,
                f"{path.name}!{nested.filename}!{mat.filename}",
            )
    except zipfile.BadZipFile as exc:
        raise BenchmarkError("Dataset ZIP is invalid") from exc


def _load_records(source: str | io.BytesIO) -> np.ndarray:
    try:
        from scipy.io import loadmat
    except ImportError as exc:
        raise BenchmarkDependencyError(
            "NASA benchmark requires requirements-benchmarks.txt"
        ) from exc
    try:
        value = loadmat(source, squeeze_me=True, struct_as_record=False)
    except (OSError, ValueError, TypeError) as exc:
        raise BenchmarkError("Cannot read NASA Milling MATLAB data") from exc
    records = np.asarray(value.get("mill"), dtype=object).reshape(-1)
    if not len(records):
        raise BenchmarkError("MATLAB data must contain a nonempty 'mill' struct array")
    if len(records) > MAXIMUM_RECORDS:
        raise BenchmarkError("MATLAB data contains too many records")
    fields = tuple(getattr(records[0], "_fieldnames", ()) or ())
    if not set(REQUIRED_FIELDS).issubset(fields):
        missing = sorted(set(REQUIRED_FIELDS) - set(fields))
        raise BenchmarkError(f"NASA Milling structure is missing fields: {', '.join(missing)}")
    return records


def _number(value: Any, field: str, *, integer: bool = False) -> float | int:
    array = np.asarray(value)
    if array.size != 1:
        raise BenchmarkError(f"{field} must be scalar")
    number = float(array.reshape(-1)[0])
    if not math.isfinite(number):
        raise BenchmarkError(f"{field} must be finite")
    if integer:
        rounded = int(round(number))
        if number != rounded:
            raise BenchmarkError(f"{field} must be an integer")
        return rounded
    return number


def _signal(value: Any, field: str) -> np.ndarray:
    raw = np.asarray(value)
    if raw.size > MAXIMUM_SIGNAL_SAMPLES:
        raise BenchmarkError(f"{field} exceeds the signal-length limit")
    signal = np.asarray(raw, dtype=np.float64).reshape(-1)
    if signal.size == 0 or not bool(np.isfinite(signal).all()):
        raise BenchmarkError(f"{field} must be a nonempty finite signal")
    return signal


def _robust_spread(values: np.ndarray) -> float:
    center = float(np.median(values))
    return float(1.4826 * np.median(np.abs(values - center)))


def _signal_summary(values: np.ndarray) -> dict[str, float | int]:
    with np.errstate(over="raise", invalid="raise"):
        try:
            rms = float(np.sqrt(np.mean(np.square(values))))
        except FloatingPointError as exc:
            raise BenchmarkError("Signal RMS is not numerically finite") from exc
    return {
        "samples": int(values.size),
        "median": float(np.median(values)),
        "rms": rms,
        "robust_spread": _robust_spread(values),
    }


def _average_ranks(values: Sequence[float]) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    order = np.argsort(array, kind="mergesort")
    ranks = np.empty(len(array), dtype=np.float64)
    position = 0
    while position < len(array):
        end = position + 1
        while end < len(array) and array[order[end]] == array[order[position]]:
            end += 1
        ranks[order[position:end]] = (position + end - 1) / 2.0
        position = end
    return ranks


def _spearman(x: Sequence[float], y: Sequence[float]) -> float | None:
    if len(x) < 3 or len(x) != len(y):
        return None
    first = _average_ranks(x)
    second = _average_ranks(y)
    if float(np.std(first)) == 0.0 or float(np.std(second)) == 0.0:
        return None
    return float(np.corrcoef(first, second)[0, 1])


def _association(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    measured = [row for row in rows if row["vb_mm"] is not None]
    result: dict[str, Any] = {"runs": len(measured), "spearman": {}}
    vb = [float(row["vb_mm"]) for row in measured]
    for signal in ANALYZED_SIGNALS:
        for metric in ("median", "rms", "robust_spread"):
            name = f"{signal}.{metric}"
            values = [float(row["signals"][signal][metric]) for row in measured]
            result["spearman"][name] = _spearman(values, vb)
    return result


def _condition_key(row: Mapping[str, Any]) -> tuple[float, float, int]:
    return float(row["doc_mm"]), float(row["feed_mm_per_rev"]), int(row["material_code"])


def _condition_summary(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[float, float, int], list[Mapping[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(_condition_key(row), []).append(row)
    result: list[dict[str, Any]] = []
    for (doc, feed, material), group in sorted(grouped.items()):
        measured = [row for row in group if row["vb_mm"] is not None]
        summaries: dict[str, dict[str, float]] = {}
        for signal in ANALYZED_SIGNALS:
            summaries[signal] = {
                metric: float(np.median([row["signals"][signal][metric] for row in group]))
                for metric in ("median", "rms", "robust_spread")
            }
        result.append(
            {
                "doc_mm": doc,
                "feed_mm_per_rev": feed,
                "material_code": material,
                "material": "cast iron" if material == 1 else "stainless steel J45",
                "runs": len(group),
                "runs_with_measured_vb": len(measured),
                "median_vb_mm": (
                    float(np.median([row["vb_mm"] for row in measured]))
                    if measured
                    else None
                ),
                "signal_medians_across_runs": summaries,
                "within_condition_association": _association(group),
            }
        )
    return result


def _confounding_summary(conditions: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ranges: dict[str, dict[str, float]] = {}
    for signal in ANALYZED_SIGNALS:
        for metric in ("median", "rms", "robust_spread"):
            values = [
                float(condition["signal_medians_across_runs"][signal][metric])
                for condition in conditions
            ]
            ranges[f"{signal}.{metric}"] = {
                "minimum_condition_median": min(values),
                "maximum_condition_median": max(values),
                "range": max(values) - min(values),
            }
    return {
        "operating_condition_groups": len(conditions),
        "between_condition_signal_ranges": ranges,
        "interpretation": (
            "Depth of cut, feed, and material vary by case and can confound pooled "
            "wear associations; within-condition results remain descriptive."
        ),
    }


def analyze_nasa_milling(dataset: str | Path) -> dict[str, Any]:
    """Parse the official artifact and compute simple per-run descriptive summaries."""

    requested = Path(dataset)
    (
        source,
        mill_mat_hash,
        source_artifact_hash,
        requested_identity,
        selected_source,
    ) = _mat_source(requested)
    records = _load_records(source)
    rows: list[dict[str, Any]] = []
    total_analyzed_signal_samples = 0
    for index, record in enumerate(records):
        case = int(_number(record.case, f"mill[{index}].case", integer=True))
        run = int(_number(record.run, f"mill[{index}].run", integer=True))
        if case < 1 or run < 1:
            raise BenchmarkError("NASA case and run identifiers must be positive")
        vb_array = np.asarray(record.VB)
        if vb_array.size != 1:
            raise BenchmarkError(f"mill[{index}].VB must be scalar")
        vb_raw = float(vb_array.reshape(-1)[0])
        vb = None if math.isnan(vb_raw) else vb_raw
        if vb is not None and (not math.isfinite(vb) or vb < 0.0):
            raise BenchmarkError("Measured flank wear must be finite and nonnegative")
        doc = float(_number(record.DOC, f"mill[{index}].DOC"))
        feed = float(_number(record.feed, f"mill[{index}].feed"))
        material = int(_number(record.material, f"mill[{index}].material", integer=True))
        if doc <= 0.0 or feed <= 0.0 or material not in {1, 2}:
            raise BenchmarkError("NASA operating-condition values are outside documented codes")
        signals: dict[str, dict[str, float | int]] = {}
        for name in ANALYZED_SIGNALS:
            signal = _signal(getattr(record, name), name)
            total_analyzed_signal_samples += int(signal.size)
            if total_analyzed_signal_samples > MAXIMUM_TOTAL_ANALYZED_SIGNAL_SAMPLES:
                raise BenchmarkError("Dataset exceeds the total analyzed-sample limit")
            signals[name] = _signal_summary(signal)
        sample_counts = {summary["samples"] for summary in signals.values()}
        if len(sample_counts) != 1:
            raise BenchmarkError("Analyzed signals in a run must have equal sample counts")
        rows.append(
            {
                "case": case,
                "run": run,
                "vb_mm": vb,
                "time_field": float(_number(record.time, f"mill[{index}].time")),
                "doc_mm": doc,
                "feed_mm_per_rev": feed,
                "material_code": material,
                "material": "cast iron" if material == 1 else "stainless steel J45",
                "signals": signals,
            }
        )
    identities = [(row["case"], row["run"]) for row in rows]
    if len(identities) != len(set(identities)):
        raise BenchmarkError("NASA case/run identities must be unique")
    conditions = _condition_summary(rows)
    measured = sum(row["vb_mm"] is not None for row in rows)
    provenance_verified = (
        source_artifact_hash == NASA_OFFICIAL_ARCHIVE_SHA256
        or mill_mat_hash == NASA_OFFICIAL_MAT_SHA256
    )
    return {
        "version": VERSION,
        "benchmark": NASA_DATASET_TITLE,
        "origin": DataOrigin.EXTERNAL_BENCHMARK.value,
        "real_data": True if provenance_verified else None,
        "synthetic_data": False if provenance_verified else None,
        "provenance_verified": provenance_verified,
        "provenance_status": (
            "VERIFIED_OFFICIAL_ARTIFACT"
            if provenance_verified
            else "UNVERIFIED_EXTERNAL_INPUT"
        ),
        "domain": "milling / machining",
        "semiconductor_data": False,
        "osat_data": False,
        "plant_validation": False,
        "production_qualified": False,
        "requested_dataset": requested_identity,
        "selected_mat_source": selected_source,
        "mill_mat_sha256": mill_mat_hash,
        "source_artifact_sha256": source_artifact_hash,
        "cases": len({row["case"] for row in rows}),
        "runs": len(rows),
        "runs_with_measured_vb": measured,
        "operating_conditions": len(conditions),
        "field_semantics": {
            "VB": "flank wear in mm; NaN denotes no supplied measurement",
            "DOC": "depth of cut in mm",
            "feed": "feed in mm/rev",
            "material": "1 = cast iron; 2 = stainless steel J45",
            "smcAC": "AC spindle-motor-current acquisition signal; physical output unit not documented in the supplied README",
            "smcDC": "DC spindle-motor-current acquisition signal; physical output unit not documented in the supplied README",
            "vib_spindle": "spindle vibration acquisition signal; physical output unit not documented in the supplied README",
        },
        "spindle_speed": {
            "compatible_time_series_present": False,
            "readme_experimental_setting": "200 m/min cutting speed, reported as 826 rev/min",
            "use_in_osat_physics": False,
            "reason": "The MATLAB struct has no spindle-speed time-series field.",
        },
        "overall_descriptive_association": _association(rows),
        "condition_summaries": conditions,
        "confounding": _confounding_summary(conditions),
        "run_summaries": rows,
        "sources": [NASA_REPOSITORY_URL, NASA_OPEN_DATA_URL],
        "claims": [
            (
                "VERIFIED EXTERNAL REAL-DATA BENCHMARK"
                if provenance_verified
                else "UNVERIFIED EXTERNAL INPUT; REAL/SYNTHETIC STATUS UNKNOWN"
            ),
            "NON-SEMICONDUCTOR MACHINING DATA",
            "NO HEALTH STATE OR MAINTENANCE TICKET IS PRODUCED",
            "NOT REAL OSAT VALIDATION",
            "NOT PROSPECTIVE PLANT VALIDATION",
            "NOT PRODUCTION QUALIFICATION",
        ],
    }


def benchmark_summary(report: Mapping[str, Any]) -> dict[str, Any]:
    """Return a concise stdout view while preserving full per-run output on request."""

    keys = (
        "version",
        "benchmark",
        "origin",
        "real_data",
        "synthetic_data",
        "provenance_verified",
        "provenance_status",
        "domain",
        "semiconductor_data",
        "osat_data",
        "plant_validation",
        "production_qualified",
        "mill_mat_sha256",
        "source_artifact_sha256",
        "cases",
        "runs",
        "runs_with_measured_vb",
        "operating_conditions",
        "field_semantics",
        "spindle_speed",
        "overall_descriptive_association",
        "condition_summaries",
        "confounding",
        "sources",
        "claims",
    )
    return {key: report[key] for key in keys}


def write_benchmark_report(report: Mapping[str, Any], output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path
