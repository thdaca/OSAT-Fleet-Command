"""Deterministic bounded reporting for POST04 results."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping
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
        "positive_count",
        "negative_count",
        "positive_prevalence",
        "average_precision_baseline",
        "average_precision_lift_over_prevalence",
        "average_precision_lift_definition",
        "positive_count_assessment",
        "discrimination_evidence",
        "threshold_transfer_evidence",
        "discrimination_evidence_context",
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
        "median_height_association_status",
        "principal_descriptive_results",
        "third_party_data_use",
        "data_use_classification",
        "parser",
        "data_quality_coverage",
        "pipeline_coverage",
        "pipeline_coverage_definition",
        "material_scoring_coverage",
        "headline_step_coverage",
        "complete_headline_material_coverage",
        "coverage_definitions",
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
