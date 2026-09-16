"""TUHH DISCO DAD3350 surface-map provenance and descriptive analysis."""
from __future__ import annotations
import importlib.metadata
import json
from pathlib import Path
import tempfile
import time
from typing import Any
import zipfile
import numpy as np
from ....pre_steps.pre03_data_provenance.pre03_data_provenance import md5_file as _md5_file, sha256_file as _sha256_file
from ..core.dataset_context import RealDataEvaluationError, RealDataNotFound, _base_report, _unverified_input
from ..core.metrics import _spearman
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
            "median_height_association_status": "DATUM_COMPARABILITY_UNVERIFIED",
            "principal_descriptive_results": [
                "detrended_height_rms",
                "detrended_mean_absolute_deviation",
                "peak_to_valley",
            ],
            "third_party_data_use": {
                "rights_statement": "Public Domain Mark 1.0",
                "rights_instrument": "public-domain marking; not CC0",
                "raw_data_in_repository_or_release": False,
                "parser": {
                    "name": "convert-keyence-files",
                    "version": KEYENCE_PARSER_VERSION,
                    "commit": KEYENCE_PARSER_COMMIT,
                    "license": "Unlicense",
                },
                "independent_validation_required": True,
            },
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
