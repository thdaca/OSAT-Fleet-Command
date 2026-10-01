"""Verify preserved historical sources separately from this implementation.

The ZIP is a read-only evidence bundle, never imported or extracted at runtime.
Source identities detect changes; behavior equivalence is checked by tests and
POST04 reproduction, not inferred from a source digest.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

from ...pre_steps.pre03_data_provenance.provenance import canonical_file_set_sha256_v2
from ...steps.step07_machine_model.model_io import identity_sha256

POST05_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = POST05_ROOT.parents[3]
FROZEN_SOURCE_ARCHIVE = POST05_ROOT / "resources/frozen_025_sources.zip"
IMPLEMENTATION_PIN = POST05_ROOT / "resources/snapshot2_implementation.json"
COMMITTED_POC_PATH = POST05_ROOT / "resources/0.2.6-poc.json"


def implementation_identity() -> dict:
    """Hash operational/scientific source and bundled inputs; UI has separate tests."""
    package = PROJECT_ROOT / "osat_edge"
    sources = [package / "pipeline.py", *[p for p in (package / "roadmap").rglob("*.py") if not any(
        part in {"tests", "research", "resources", "__pycache__"} for part in p.parts
    )]]
    inputs = [p for p in package.rglob("*") if p.is_file()
              and "resources" in p.parts and p.suffix in {".json", ".csv", ".zip"}
              and p not in {IMPLEMENTATION_PIN, COMMITTED_POC_PATH}
              and p.name != "0.2.6-reproducer.json"]
    items = [(p.relative_to(PROJECT_ROOT).as_posix(), p.read_bytes())
             for p in sorted(set(sources + inputs))]
    return {
        "method": "CANONICAL_FILE_SET_SHA256_V2",
        "file_count": len(items),
        "sha256": canonical_file_set_sha256_v2(items),
        "meaning": "current source and input identity; not REAL_OSAT provenance or behavioral proof",
    }


def frozen_lineage() -> dict:
    manifest = json.loads((POST05_ROOT / "resources/frozen_025_science.json").read_bytes())
    try:
        with zipfile.ZipFile(FROZEN_SOURCE_ARCHIVE) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)) or set(names) != set(manifest["files"]):
                raise ValueError("Preserved frozen-source file set changed")
            changed = [name for name, expected in manifest["files"].items()
                       if hashlib.sha256(archive.read(name)).hexdigest() != expected]
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        raise ValueError("Preserved frozen-source archive is unavailable or corrupt") from exc
    if changed:
        raise ValueError("Preserved frozen scientific/source bytes changed: " + ", ".join(changed))

    # Reorganization changes source identity. Keep a distinct current pin and
    # reject unreviewed drift rather than comparing new code with old hashes.
    approved = json.loads(IMPLEMENTATION_PIN.read_bytes())
    current = implementation_identity()
    if approved.get("implementation_identity") != current:
        raise ValueError("Current implementation/source identity differs from the snapshot 2 pin")

    evidence_path = POST05_ROOT.parent / "post04_real_data_evaluation/resources/0.2.5-real-data.json"
    evidence_hash = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    expected_hash = manifest["files"][evidence_path.relative_to(PROJECT_ROOT).as_posix()]
    if evidence_hash != expected_hash:
        raise ValueError("Frozen 0.2.5 scientific evidence bytes changed")
    evidence = json.loads(evidence_path.read_bytes())
    return {
        "status": "PASS",
        "baseline": manifest["baseline"],
        "baseline_zip_sha256": manifest["archive_sha256"],
        "frozen_file_count": len(manifest["files"]),
        "frozen_manifest_sha256": identity_sha256(manifest),
        "preserved_source_archive_sha256": hashlib.sha256(FROZEN_SOURCE_ARCHIVE.read_bytes()).hexdigest(),
        "current_implementation_identity": current,
        "external_evidence_artifact_sha256": evidence_hash,
        "external_evidence_release": evidence["release_version"],
        "external_evidence_summary": evidence["summary"],
        "st_awfd_interpretation": evidence["st_awfd_discrimination_interpretation"],
        "external_results": [{key: item[key] for key in (
            "dataset", "status", "source_sha256", "continuous_metrics", "discrimination_evidence",
            "threshold_transfer_evidence", "principal_descriptive_results", "operational_ticket_count",
        ) if key in item} for item in evidence["results"]],
        "external_data_used_for_operational_model": False,
        "verification_scope": "preserved historical bytes, unchanged evidence and pinned current source; behavior tests and POST04 reproduction are separate checks",
    }
