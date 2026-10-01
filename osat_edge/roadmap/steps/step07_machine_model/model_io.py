"""Small deterministic JSON artifact, not a registry or executable pickle.

The digest covers canonical payload bytes (excluding the digest itself). It
detects corruption, not forgery or scientific validity. Callers must supply the
expected feature/calibration identities from their approved onboarding record.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Mapping

import numpy as np

from ...pre_steps.pre01_common.contracts import (
    DataOrigin, EquipmentState, MachineIdentity, RuntimeMode, VERSION,
)
from .model import ContextModel, MachineModel, validate_machine_model

SCHEMA_VERSION = "OSAT_EXACT_MACHINE_MODEL_V1"
VALIDATION_STATUS = "ACCEPTED_RESEARCH_ONLY"
MAXIMUM_ARTIFACT_BYTES = 1_000_000


class MachineModelArtifactError(ValueError):
    """An artifact cannot be used; callers must leave the machine uncalibrated."""


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def identity_sha256(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def feature_contract(model: MachineModel) -> dict[str, list[list[str]]]:
    return {
        state.value: [list(item) for item in zip(
            context.feature_names, context.subsystems, context.kinds, strict=True
        )]
        for state, context in sorted(model.contexts.items(), key=lambda item: item[0].value)
    }


def physics_identity(model: MachineModel) -> str:
    return identity_sha256({name: dict(values) for name, values in model.physics_parameters.items()})


@dataclass(frozen=True)
class LoadedMachineModel:
    model: MachineModel
    artifact_sha256: str
    source_sha256: str
    calibration_sha256: str
    validation_sha256: str


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise MachineModelArtifactError("Duplicate JSON key")
        result[key] = value
    return result


def load_machine_model(
    path: str | Path, *, active_machine: MachineIdentity, runtime_mode: RuntimeMode,
    expected_feature_contract: Mapping, expected_physics_sha256: str,
    expected_source_sha256: str, expected_calibration_sha256: str,
    expected_validation_sha256: str,
) -> LoadedMachineModel:
    """Fail closed on identity, contract, validation, numeric or byte corruption."""
    try:
        with Path(path).open("rb") as stream:
            raw = stream.read(MAXIMUM_ARTIFACT_BYTES + 1)
        if len(raw) > MAXIMUM_ARTIFACT_BYTES:
            raise ValueError("Artifact exceeds size bound")
        envelope = json.loads(raw, object_pairs_hook=_unique_object)
        if set(envelope) != {"payload", "artifact_sha256"}:
            raise ValueError("Unexpected artifact envelope")
        payload = envelope["payload"]
        digest = identity_sha256(payload)
        if not hmac.compare_digest(digest, envelope["artifact_sha256"]):
            raise ValueError("Artifact SHA-256 mismatch")
        if set(payload) != {
            "schema_version", "software_version", "machine", "origin", "source_sha256",
            "calibration_sha256", "validation_sha256", "validation_status",
            "feature_contract", "contexts", "physics_parameters", "physics_sha256",
        }:
            raise ValueError("Unexpected model schema fields")
        if payload["schema_version"] != SCHEMA_VERSION or payload["software_version"] != VERSION:
            raise ValueError("Incompatible model schema/software version")
        if payload["validation_status"] != VALIDATION_STATUS:
            raise ValueError("Model has not passed separate research validation")
        for field, expected in (
            ("source_sha256", expected_source_sha256),
            ("calibration_sha256", expected_calibration_sha256),
            ("validation_sha256", expected_validation_sha256),
            ("physics_sha256", expected_physics_sha256),
        ):
            if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
                raise ValueError(f"Invalid expected {field}")
            if payload[field] != expected:
                raise ValueError(f"Mismatched {field}")
        if payload["feature_contract"] != expected_feature_contract:
            raise ValueError("Incompatible feature contract")
        contexts = {}
        for state, item in payload["contexts"].items():
            if set(item) != {"feature_names", "subsystems", "kinds", "center", "scale"}:
                raise ValueError("Unexpected context fields")
            if any(type(x) not in (int, float) for field in ("center", "scale") for x in item[field]):
                raise ValueError("Model parameters must be numbers, not booleans/strings")
            if any(not isinstance(x, str) or not x for field in (
                "feature_names", "subsystems", "kinds"
            ) for x in item[field]):
                raise ValueError("Invalid feature metadata")
            contexts[EquipmentState(state)] = ContextModel(
                EquipmentState(state), tuple(item["feature_names"]), tuple(item["subsystems"]),
                tuple(item["kinds"]), np.asarray(item["center"]), np.asarray(item["scale"]),
            )
        if any(type(value) not in (int, float) for values in payload["physics_parameters"].values()
               for value in values.values()):
            raise ValueError("Physics parameters must be numbers, not booleans/strings")
        model = MachineModel(MachineIdentity(**payload["machine"]), DataOrigin(payload["origin"]),
                             contexts, payload["physics_parameters"])
        if model.origin is DataOrigin.EXTERNAL_BENCHMARK:
            raise ValueError("External benchmarks have no operational model authority")
        validate_machine_model(model, active_machine, runtime_mode)
        if feature_contract(model) != payload["feature_contract"] or physics_identity(model) != payload["physics_sha256"]:
            raise ValueError("Inconsistent feature/physics identity")
        return LoadedMachineModel(model, digest, payload["source_sha256"],
                                  payload["calibration_sha256"], payload["validation_sha256"])
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError) as exc:
        raise MachineModelArtifactError(f"Machine-model artifact rejected: {exc}") from exc


def save_machine_model(
    model: MachineModel, path: str | Path, *, source_sha256: str,
    calibration_sha256: str, validation_sha256: str, validation_status: str,
) -> str:
    """Persist a separately validated model, verify temporary bytes, then replace.

    This function does not certify a model. Validation lineage must be supplied
    by the caller; a SHA-256 is not a signature or evidence of plant health.
    """
    payload = {
        "schema_version": SCHEMA_VERSION, "software_version": VERSION,
        "machine": asdict(model.machine), "origin": model.origin.value,
        "source_sha256": source_sha256, "calibration_sha256": calibration_sha256,
        "validation_sha256": validation_sha256, "validation_status": validation_status,
        "feature_contract": feature_contract(model),
        "contexts": {state.value: {
            "feature_names": list(context.feature_names), "subsystems": list(context.subsystems),
            "kinds": list(context.kinds), "center": context.center.tolist(), "scale": context.scale.tolist(),
        } for state, context in model.contexts.items()},
        "physics_parameters": {name: dict(values) for name, values in model.physics_parameters.items()},
        "physics_sha256": physics_identity(model),
    }
    digest = identity_sha256(payload)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(canonical_bytes({"payload": payload, "artifact_sha256": digest}))
        load_machine_model(
            temporary, active_machine=model.machine, runtime_mode=RuntimeMode.SIMULATION,
            expected_feature_contract=feature_contract(model), expected_physics_sha256=physics_identity(model),
            expected_source_sha256=source_sha256, expected_calibration_sha256=calibration_sha256,
            expected_validation_sha256=validation_sha256,
        )
        os.replace(temporary, destination)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return digest
