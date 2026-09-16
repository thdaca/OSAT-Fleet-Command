# Frozen synthetic reference replay

Dataset ID: `osat-reference-fleet-001`  
Schema: `1.0`  
Release generator: OSAT Fleet Command `0.2.3`

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

The one reference machine is the synthetic demo identity `DEMO-WS-01`
for the existing `WS-01` wafer-saw profile. The timeline moves
through healthy operation, optional-channel absence, required-channel staleness
and recovery, an out-of-calibration spindle-speed interval that makes the
reviewed residual abstain, return in-domain, and a synthetic positive-load
residual that naturally exercises deterministic health and a demo-only ticket.

Regenerate only when intentionally revising the frozen artifact:

```powershell
.venv\Scripts\python tools\generate_reference_replay.py
```
