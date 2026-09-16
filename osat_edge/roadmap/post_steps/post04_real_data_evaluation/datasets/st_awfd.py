"""STMicroelectronics ST-AWFD D1 and D2 benchmark evaluation."""
from __future__ import annotations
import datetime as dt
from pathlib import Path
import time
from typing import Any, Mapping, Sequence
import zipfile
import numpy as np
from ....pre_steps.pre01_common.pre01_common import EquipmentState, MachineIdentity
from ....steps.step02_physical_features.step02_physical_features import Feature, FeatureSet
from ....steps.step07_machine_model.step07_machine_model import evaluate_machine_model_numerically
from ....pre_steps.pre03_data_provenance.pre03_data_provenance import sha256_file as _sha256_file
from ..core.dataset_context import RealDataEvaluationError, RealDataNotFound, _base_report, _unverified_input
from ..core.metrics import _binary_threshold_metrics, _continuous_binary_metrics, _score_distribution
from ..core.model_bridge import _fit_nominal_benchmark_model
ST_AWFD_SOURCE_COMMIT = "54be5cc91b83615240710bda9745f51c984d10c5"
ST_AWFD_LICENSE = "CC BY-NC-SA 4.0"
LOW_POSITIVE_COUNT_THRESHOLD = 10
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


def _st_discrimination_evidence(dataset_id: str, positive_count: int) -> str:
    """Interpret D1's sparse positives without changing any measured score."""

    if dataset_id == "st-awfd-d1" and positive_count < LOW_POSITIVE_COUNT_THRESHOLD:
        return "INDICATIVE_EXTERNAL_DISCRIMINATION_DESCRIPTIVE_ONLY"
    return "SUPPORTED_EXTERNALLY_FOR_STEP07_CONTINUOUS_DISCRIMINATION"


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
    continuous_metrics = _continuous_binary_metrics(labels, location)
    positive_count = len(abnormal)
    negative_count = len(normal)
    positive_prevalence = positive_count / len(labels) if labels else None
    average_precision = continuous_metrics["average_precision"]
    average_precision_lift = (
        average_precision / positive_prevalence
        if average_precision is not None and positive_prevalence
        else None
    )
    scored_headline_steps = sum(
        item["status"] == "SCORED" for item in step_results
    )
    material_scoring_coverage = (
        len(scored_materials) / len(held_out_materials)
        if held_out_materials
        else None
    )
    headline_step_coverage = scored_headline_steps / len(spec["headline_steps"])
    complete_materials = sum(
        len(location_scores[material_id]) == len(spec["headline_steps"])
        for material_id in held_out_materials
    )
    complete_headline_material_coverage = (
        complete_materials / len(held_out_materials)
        if held_out_materials
        else None
    )
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
            "continuous_metrics": continuous_metrics,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "positive_prevalence": positive_prevalence,
            "average_precision_baseline": positive_prevalence,
            "average_precision_lift_over_prevalence": average_precision_lift,
            "average_precision_lift_definition": (
                "average_precision / positive_prevalence"
            ),
            "positive_count_assessment": (
                "LOW_POSITIVE_COUNT_DESCRIPTIVE_ONLY"
                if positive_count < LOW_POSITIVE_COUNT_THRESHOLD
                else "DESCRIPTIVE_EXTERNAL_BENCHMARK"
            ),
            "discrimination_evidence": _st_discrimination_evidence(
                dataset_id, positive_count
            ),
            "threshold_transfer_evidence": (
                "NOT_SUPPORTED_FOR_FROZEN_STEP09_THRESHOLD_TRANSFER_OR_CALIBRATION"
            ),
            "discrimination_evidence_context": (
                "AUROC is based on only two abnormal held-out MaterialIDs and is statistically fragile."
                if positive_count == 2
                else "Observed on the official held-out MaterialID split without threshold tuning."
            ),
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
            "material_scoring_coverage": material_scoring_coverage,
            "headline_step_coverage": headline_step_coverage,
            "complete_headline_material_coverage": complete_headline_material_coverage,
            "coverage_definitions": {
                "material_scoring_coverage": (
                    "held-out MaterialIDs with at least one location score / all held-out MaterialIDs"
                ),
                "headline_step_coverage": (
                    "configured headline StepIDs scored / configured headline StepIDs"
                ),
                "complete_headline_material_coverage": (
                    "held-out MaterialIDs scored for every configured headline StepID / all held-out MaterialIDs"
                ),
            },
            "pipeline_coverage": material_scoring_coverage,
            "pipeline_coverage_definition": (
                "legacy evidence-schema alias for material_scoring_coverage"
            ),
            "data_use_classification": "NONCOMMERCIAL_RESEARCH_BENCHMARK",
            "third_party_data_use": {
                "rights_statement": "CC BY-NC-SA 4.0",
                "raw_data_in_repository_or_release": False,
                "commercial_reexecution_or_redistribution": (
                    "requires permission or legal/license review"
                ),
                "fleet_command_code_sharealike_claim": False,
            },
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
