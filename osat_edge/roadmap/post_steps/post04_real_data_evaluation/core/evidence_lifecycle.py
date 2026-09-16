"""Historical integrity and current deterministic evidence reproduction."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping
from ....pre_steps.pre01_common.pre01_common import DataOrigin, VERSION
from ....pre_steps.pre03_data_provenance.pre03_data_provenance import sha256_file as _sha256_file
from .dataset_context import DATASET_ORDER, POST04_ROOT, RealDataEvaluationError
from .reporting import deterministic_scientific_bytes, deterministic_scientific_sha256
HISTORICAL_EVIDENCE_PATH = POST04_ROOT / "resources" / "0.2.4-real-data.json"
CURRENT_EVIDENCE_PATH = POST04_ROOT / "resources" / "0.2.5-real-data.json"
COMMITTED_EVIDENCE_PATH = CURRENT_EVIDENCE_PATH
HISTORICAL_EVIDENCE_SHA256 = "371b9f6c40f2185a5d505f373483973f7f5974c276890d0616b9a715706014b3"
THIRD_PARTY_DATA_USE_PATH = POST04_ROOT / "resources" / "THIRD_PARTY_DATA_USE.json"
SNAPSHOT4_SCIENTIFIC_PAYLOAD_SHA256 = (
    "61963b9a0de672f5e698d30442d5e5c4c81fce299e9a66ca2ef8b76074f11132"
)
SNAPSHOT4_EVIDENCE_ARTIFACT_SHA256 = (
    "eb301b10f2f8da993a2117d143c0af77f44bb75999325ca55b666f53e18557ed"
)
SNAPSHOT5_REPORTING_FIELDS = frozenset(
    {
        "average_precision_baseline",
        "average_precision_lift_over_prevalence",
        "average_precision_lift_definition",
        "complete_headline_material_coverage",
        "coverage_definitions",
        "data_use_classification",
        "discrimination_evidence",
        "discrimination_evidence_context",
        "headline_step_coverage",
        "material_scoring_coverage",
        "median_height_association_status",
        "negative_count",
        "pipeline_coverage_definition",
        "positive_count",
        "positive_count_assessment",
        "positive_prevalence",
        "principal_descriptive_results",
        "third_party_data_use",
        "threshold_transfer_evidence",
    }
)


def snapshot4_scientific_payload_sha256(record: Mapping[str, Any]) -> str:
    """Hash every Snapshot 4 evidence value except code identity and new metadata."""

    value = json.loads(json.dumps(record))
    value.pop("evaluator_sha256", None)
    value.pop("deterministic_comparison_report_sha256", None)
    value.pop("snapshot4_scientific_payload_sha256", None)
    value.pop("snapshot4_evidence_artifact_sha256", None)
    value.pop("third_party_data_use_inventory", None)
    for result in value.get("results", []):
        for field in SNAPSHOT5_REPORTING_FIELDS:
            result.pop(field, None)
    payload = (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def snapshot4_result_sha256(result: Mapping[str, Any]) -> str:
    """Hash one result after removing only Snapshot 5 reporting additions."""

    value = dict(result)
    for field in SNAPSHOT5_REPORTING_FIELDS:
        value.pop(field, None)
    payload = (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def evaluator_source_sha256() -> str:
    """Hash the complete organized POST04 implementation, excluding tests."""
    sources = [
        POST04_ROOT / "post04_real_data_evaluation.py",
        *sorted((POST04_ROOT / "core").glob("*.py")),
        *sorted((POST04_ROOT / "datasets").glob("*.py")),
    ]
    digest = hashlib.sha256()
    for source in sources:
        relative = source.relative_to(POST04_ROOT).as_posix().encode("utf-8")
        content = source.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(hashlib.sha256(content).digest())
    return digest.hexdigest()
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
        "source_field_coverage",
        "surface_maps",
        "feed_velocity_spearman",
        "median_height_association_status",
        "principal_descriptive_results",
        "third_party_data_use",
        "data_use_classification",
        "data_quality_coverage",
        "pipeline_coverage",
        "pipeline_coverage_definition",
        "material_scoring_coverage",
        "headline_step_coverage",
        "complete_headline_material_coverage",
        "coverage_definitions",
        "operational_ticket_count",
        "limitations",
    )
    results = [
        {key: item[key] for key in result_keys if key in item}
        for item in report["datasets"]
    ]
    record = {
        "schema_version": "1.0",
        "release_version": VERSION,
        "origin": DataOrigin.EXTERNAL_BENCHMARK.value,
        "historical_artifact": {
            "name": HISTORICAL_EVIDENCE_PATH.name,
            "sha256": HISTORICAL_EVIDENCE_SHA256,
            "reproduced_as_current": False,
        },
        "evaluator_sha256": evaluator_source_sha256(),
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
    observed_snapshot4_hash = snapshot4_scientific_payload_sha256(record)
    if (
        tuple(report.get("dataset_order", ())) == DATASET_ORDER
        and observed_snapshot4_hash != SNAPSHOT4_SCIENTIFIC_PAYLOAD_SHA256
    ):
        raise RealDataEvaluationError(
            "SNAPSHOT 4 SCIENTIFIC PAYLOAD DRIFT: a pre-existing evidence value changed"
        )
    record["snapshot4_scientific_payload_sha256"] = observed_snapshot4_hash
    record["snapshot4_evidence_artifact_sha256"] = (
        SNAPSHOT4_EVIDENCE_ARTIFACT_SHA256
    )
    record["third_party_data_use_inventory"] = {
        "path": THIRD_PARTY_DATA_USE_PATH.name,
        "sha256": _sha256_file(THIRD_PARTY_DATA_USE_PATH),
    }
    return record
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
    evaluator_hash = evaluator_source_sha256()
    from ..post04_real_data_evaluation import evaluate_all_real_data

    regenerated = evaluate_all_real_data(external_root)
    report_hash = deterministic_scientific_sha256(regenerated)
    regenerated_evidence = current_real_data_evidence_record(regenerated)
    drift: list[str] = []
    if expected.get("release_version") != VERSION:
        drift.append("release version")
    if expected.get("evaluator_sha256") != evaluator_hash:
        drift.append("evaluator SHA-256")
    if expected.get("deterministic_comparison_report_sha256") != report_hash:
        drift.append("deterministic comparison report SHA-256")
    if expected.get("summary") != regenerated.get("summary"):
        drift.append("summary")
    if expected != regenerated_evidence:
        drift.append("complete deterministic aggregate evidence")
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
        "snapshot4_scientific_payload_sha256": regenerated_evidence[
            "snapshot4_scientific_payload_sha256"
        ],
        "datasets_checked": len(expected.get("results", [])),
        "operational_tickets": regenerated["summary"]["operational_tickets"],
    }
    if historical is not None:
        result["historical_artifact_integrity"] = historical
    return result
