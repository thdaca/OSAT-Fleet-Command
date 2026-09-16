"""Deterministically regenerate the frozen synthetic reference replay artifact."""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from osat_edge.common import DataOrigin, RuntimeMode, VERSION  # noqa: E402
from osat_edge.demo import _demo_identity, _fit_demo_model, _stable_center  # noqa: E402
from osat_edge.machines import STATIONS  # noqa: E402
from osat_edge.roadmap.step01_physics_library import SPEED_HIGH  # noqa: E402


OUTPUT = ROOT / "examples" / "reference_replay"
START = dt.datetime(2026, 2, 2, 14, 0, tzinfo=dt.timezone.utc)
DATASET_ID = "osat-reference-fleet-001"
SCHEMA_VERSION = "1.0"


def _timestamp(seconds: float) -> str:
    value = START + dt.timedelta(seconds=seconds)
    if value.microsecond:
        return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _healthy_value(channel: str, unit: str, seconds: float) -> float:
    center = _stable_center(channel, unit)
    amplitude = max(abs(center) * 0.002, 0.002)
    divisor = 13.0 if channel == "spindle_speed" else 11.0
    value = center + amplitude * math.sin(seconds / divisor)
    if channel == "spindle_current":
        speed_center = _stable_center("spindle_speed", "RPM")
        speed = speed_center + speed_center * 0.002 * math.sin(seconds / 13.0)
        value = center + 0.00004 * (speed - speed_center)
    return value


def generate() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    station = STATIONS["wafer_saw"]
    identity = _demo_identity(station)
    model = _fit_demo_model(identity, station)
    speed_high = model.physics_parameters["spindle.current_speed_residual"][SPEED_HIGH]
    external_ids = {
        spec.name: f"REF-{index:02d}-{spec.name.upper().replace('_', '-')}"
        for index, spec in enumerate(station.channels, start=1)
    }
    mapping = {
        "dataset_id": DATASET_ID,
        "schema_version": SCHEMA_VERSION,
        "origin": DataOrigin.SYNTHETIC.value,
        "machine_id": identity.machine_id,
        "mappings": [
            {
                "canonical_channel": spec.name,
                "source_id": external_ids[spec.name],
                "unit": spec.unit,
            }
            for spec in station.channels
        ],
    }
    _json(OUTPUT / "source_mapping.json", mapping)

    contexts = [
        {
            "timestamp_utc": _timestamp(float(second)),
            "machine_id": identity.machine_id,
            "equipment_state": "PROCESSING",
        }
        for second in range(251)
    ]
    with (OUTPUT / "context.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["timestamp_utc", "machine_id", "equipment_state"]
        )
        writer.writeheader()
        writer.writerows(contexts)

    telemetry: list[dict[str, str]] = []
    for spec in station.channels:
        sample = 0.0
        while sample <= 250.0 + 1e-9:
            missing_optional = spec.name == "spindle_vibration" and 75.0 <= sample <= 82.0
            stale_required = spec.name == "spindle_current" and 81.0 <= sample <= 88.0
            if not missing_optional and not stale_required:
                value = _healthy_value(spec.name, spec.unit, sample)
                if 105.0 <= sample <= 170.0 and spec.name == "spindle_speed":
                    value = speed_high + 50.0
                if 105.0 <= sample <= 170.0 and spec.name == "spindle_current":
                    speed_center = _stable_center("spindle_speed", "RPM")
                    value = _stable_center("spindle_current", "A") + 0.00004 * (
                        speed_high + 50.0 - speed_center
                    )
                if sample >= 185.0:
                    progress = min((sample - 185.0) / 50.0, 1.0)
                    if spec.name == "spindle_current":
                        value += 0.0012 * progress
                    elif spec.name == "spindle_vibration":
                        value += 0.01 * progress
                telemetry.append(
                    {
                        "timestamp_utc": _timestamp(sample),
                        "machine_id": identity.machine_id,
                        "source_id": external_ids[spec.name],
                        "value": format(value, ".12g"),
                        "unit": spec.unit,
                    }
                )
            sample = round(sample + spec.period_seconds, 10)
    telemetry.sort(
        key=lambda row: (
            dt.datetime.fromisoformat(row["timestamp_utc"].replace("Z", "+00:00")),
            row["source_id"],
        )
    )
    with (OUTPUT / "telemetry.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["timestamp_utc", "machine_id", "source_id", "value", "unit"],
        )
        writer.writeheader()
        writer.writerows(telemetry)

    checkpoints = {
        "dataset_id": DATASET_ID,
        "schema_version": SCHEMA_VERSION,
        "note": "These expectations support tests and review; inference never reads them as decisions.",
        "expected_final_state": "CRITICAL",
        "expected_subsystem": "spindle",
        "expected_ticket_priority": "URGENT",
        "checkpoints": [
            {"name": "healthy", "timestamp_utc": _timestamp(70), "expected": {"health": "NORMAL", "telemetry_valid": True}},
            {"name": "optional_missing", "timestamp_utc": _timestamp(81), "expected": {"telemetry_valid": True}},
            {"name": "required_stale", "timestamp_utc": _timestamp(87), "expected": {"health": "UNKNOWN", "telemetry_valid": False}},
            {"name": "recovered", "timestamp_utc": _timestamp(96), "expected": {"health": "NORMAL", "telemetry_valid": True}},
            {"name": "physics_abstains", "timestamp_utc": _timestamp(170), "expected": {"physics_residual_present": False}},
            {"name": "physics_resumes", "timestamp_utc": _timestamp(180), "expected": {"physics_residual_present": True}},
            {"name": "watch", "timestamp_utc": _timestamp(235), "expected": {"health": "WATCH"}},
            {"name": "degraded_ticket", "timestamp_utc": _timestamp(240), "expected": {"health": "DEGRADED", "ticket_created": True}},
            {"name": "critical_ticket", "timestamp_utc": _timestamp(250), "expected": {"health": "CRITICAL", "ticket_count": 1}},
        ],
    }
    _json(OUTPUT / "expected_checkpoints.json", checkpoints)
    readme = f"""# Frozen synthetic reference replay

Dataset ID: `{DATASET_ID}`  
Schema: `{SCHEMA_VERSION}`  
Release generator: OSAT Fleet Command `{VERSION}`

This small, deterministic artifact is **SYNTHETIC REFERENCE REPLAY** data. It
uses `REAL_REPLAY` execution semantics so students can inspect the real replay,
mapping, telemetry, physics, exact-machine, health, evidence, and demo-ticket
path without representing the inputs as real equipment evidence.

It is not real OSAT data, plant validation, production qualification, or a
failure-prediction benchmark. The values contain no recipe, PPID, wafer map,
geometry, proprietary process window, or calibration constant from equipment.

`telemetry.csv` is asynchronous long-form telemetry. `context.csv` keeps
equipment state separate. `source_mapping.json` is the explicit fail-closed
external-ID mapping. `expected_checkpoints.json` is reviewed test metadata; it
does not control inference. `manifest.json` records provenance and SHA-256
checksums for the other four files.

The one reference machine is the synthetic demo identity `{identity.machine_id}`
for the existing `{identity.station_id}` wafer-saw profile. The timeline moves
through healthy operation, optional-channel absence, required-channel staleness
and recovery, an out-of-calibration spindle-speed interval that makes the
reviewed residual abstain, return in-domain, and a synthetic positive-load
residual that naturally exercises deterministic health and a demo-only ticket.

Regenerate only when intentionally revising the frozen artifact:

```powershell
.venv\\Scripts\\python tools\\generate_reference_replay.py
```
"""
    (OUTPUT / "README.md").write_text(readme, encoding="utf-8")

    manifest = {
        "dataset_id": DATASET_ID,
        "schema_version": SCHEMA_VERSION,
        "release_version": VERSION,
        "title": "OSAT Fleet Command frozen synthetic reference replay",
        "origin": DataOrigin.SYNTHETIC.value,
        "runtime_mode": RuntimeMode.REAL_REPLAY.value,
        "classification": ["FROZEN", "EDUCATIONAL", "PIPELINE-REFERENCE DATA"],
        "production_qualified": False,
        "machine": {
            "machine_id": identity.machine_id,
            "family": identity.family,
            "station_id": identity.station_id,
            "name": f"Synthetic reference {identity.name}",
        },
        "timeline": {"start_utc": _timestamp(0), "end_utc": _timestamp(250)},
        "phases": [
            {"name": "healthy_stable", "start_seconds": 0, "end_seconds": 65},
            {"name": "healthy_variation", "start_seconds": 66, "end_seconds": 74},
            {"name": "optional_missing", "start_seconds": 75, "end_seconds": 82},
            {"name": "required_stale", "start_seconds": 81, "end_seconds": 88},
            {"name": "recovery", "start_seconds": 89, "end_seconds": 104},
            {"name": "physics_outside_calibration", "start_seconds": 105, "end_seconds": 170},
            {"name": "physics_in_domain", "start_seconds": 171, "end_seconds": 184},
            {"name": "positive_load_residual", "start_seconds": 185, "end_seconds": 250},
        ],
        "files": {
            name: _sha256(OUTPUT / name)
            for name in (
                "telemetry.csv",
                "context.csv",
                "source_mapping.json",
                "expected_checkpoints.json",
            )
        },
        "claims": [
            "SYNTHETIC REFERENCE REPLAY",
            "NOT REAL OSAT DATA",
            "NOT PLANT VALIDATION",
            "NOT PRODUCTION QUALIFICATION",
        ],
    }
    _json(OUTPUT / "manifest.json", manifest)


if __name__ == "__main__":
    generate()
