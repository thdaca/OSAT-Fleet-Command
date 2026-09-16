# Frozen synthetic reference replay

OSAT Fleet Command 0.2.3 bundles exactly one small reference artifact at
`examples/reference_replay/`. Its dataset ID is
`osat-reference-fleet-001`.

The provenance is intentionally two-dimensional:

- runtime mode: `REAL_REPLAY`;
- data origin: `SYNTHETIC`.

This is a **SYNTHETIC REFERENCE REPLAY** and a development-only pipeline
demonstration. It is not real OSAT data, plant validation, production
qualification, or evidence of failure-prediction performance.

## Files and integrity boundary

`manifest.json` fixes the dataset identity, release schema, provenance,
machine identity, phase descriptions, and SHA-256 checksums. It does not hash
itself. `telemetry.csv` is asynchronous long-form telemetry with exactly these
columns: timestamp, machine, external source ID, value, and unit.
`context.csv` separately records equipment state. `source_mapping.json`
explicitly maps each external fixture ID to one approved canonical channel.
`expected_checkpoints.json` documents reviewed expectations for tests; the
pipeline never reads an expected health value to make a decision.

The SHA-256 values provide checksum/integrity verification for the frozen
files. They are not signatures, authentication, or proof of data origin.

The loader fails closed on missing or malformed files, unsupported IDs or
schema versions, bad checksums, wrong machine/family/station, unknown source
IDs, mismatched units, non-finite values, non-UTC timestamps, duplicates,
non-increasing per-channel time, and invalid equipment states.

## Run

```powershell
.venv\Scripts\python -m osat_edge.cli reference-replay
```

The loader creates the existing `ReplayTelemetrySource`, which exhausts
explicitly at the end of the history. The pipeline uses the existing frozen
station profile, telemetry store, physical feature/residual path,
exact-machine model, subsystem-first health engine, structured fault evidence,
and deterministic ticket workflow. The exact-machine model is a separate
deterministic synthetic healthy calibration built by the existing demo
calibration path; it is not trained from the abnormal replay and is reported as
synthetic research calibration.

## Actual frozen trace

The checked-in artifact has 1,509 telemetry rows, 251 context rows, and 494
asynchronous replay ticks. All 1,509 telemetry rows and 251 context rows are
accepted; zero are rejected. Because loading is fail-closed, an invalid fixture
produces an error rather than partial ingestion. On the accepted 0.2.3 code it
produces:

- initial `UNKNOWN` while the 60-second feature window matures, then `NORMAL`;
- optional spindle-vibration absence while required telemetry remains valid;
- stale required spindle current at `2026-02-02T14:01:25.500Z`, producing invalid,
  unobservable telemetry and `UNKNOWN`;
- recovered valid telemetry and `NORMAL` by `2026-02-02T14:01:31Z`;
- no current/speed physics residual at `2026-02-02T14:02:50Z` after the speed
  history remains outside the fitted no-extrapolation envelope;
- physics residual recovery after returning in-domain;
- `WATCH` at `2026-02-02T14:03:53.500Z`, `DEGRADED` at
  `2026-02-02T14:04:00Z`, and `CRITICAL` at
  `2026-02-02T14:04:09.500Z` from synthetic spindle evidence;
- one deterministic demo-only ticket, created HIGH at the DEGRADED transition
  and updated to URGENT at the CRITICAL transition.

These are observed software-pipeline outcomes for the frozen fixture. They do
not calibrate universal equipment thresholds or prove a physical fault.

## One worked data trace

At the DEGRADED transition, the original long-form CSV row is:

```csv
2026-02-02T14:04:00Z,DEMO-WS-01,REF-01-SPINDLE-CURRENT,2.40370980725,A
```

The reviewed mapping resolves `REF-01-SPINDLE-CURRENT` to the existing
canonical `spindle_current` channel and the profile-approved `WS-SV-01` source
identity. The current 60-second window yields
`spindle_current.median = 2.40334013653 A`. After timestamp alignment with the
canonical spindle-speed stream, the existing Step-03 relation yields
`spindle.electromechanical_load_residual_a.median = 0.000384000017 A`.

The separate synthetic exact-machine model compares that residual with its
healthy calibration and reports `+3.84` robust scales, with a deviation score
of `0.678899`. The unchanged subsystem-first health engine transitions the
machine to `DEGRADED`, localized to `spindle`. Step 10 records signed structured
evidence, and the deterministic maintenance branch creates ticket
`WS-01-20260202T140400000000` with HIGH priority and `demo_only: true`. The
later CRITICAL transition updates that same ticket to URGENT. The original
fault evidence retains `runtime_mode: REAL_REPLAY`; the ticket is authorized
only because this checksum-verified frozen synthetic fixture is explicitly
eligible for demo-only ticket generation.

## Intentional regeneration

The runtime never regenerates its input. If a future release intentionally
changes the teaching artifact, run:

```powershell
.venv\Scripts\python tools\generate_reference_replay.py
```

Review the diff, verify the new checksums and observed checkpoints, and rerun
the complete test suite. Do not edit expected checkpoints merely to conceal an
algorithm or fixture regression.
