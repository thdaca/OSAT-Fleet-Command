# OSAT Fleet Command 0.2.4

**RESEARCH / DEVELOPMENT BUILD — not production qualified**

Release title: **EXTERNAL REAL-DATA EVALUATION**

Version 0.2.4 adds an isolated offline evaluator for explicitly supplied real
external data. The 0.2.3 inference method, thresholds, canonical stations,
demo, reference replay, UI, security boundary, and ticket authority are not
tuned or redesigned.

OSAT Fleet Command is a small, edge-oriented teaching and research implementation for exploring equipment-health evidence in semiconductor back-end manufacturing. It keeps deterministic health and maintenance decisions separate from optional language-model enrichment.

## What this build does

The repository follows one visible path:

1. reviewed physics relations;
2. robust physical features;
3. physical residuals;
4. optional same-family data and risk model;
5. exact-machine history and model;
6. asynchronous live or replay telemetry;
7. subsystem-first deterministic health;
8. structured fault evidence;
9. deterministic demo-only maintenance ticket for simulation or the bundled
   synthetic reference replay;
10. optional local manual retrieval and local-LLM wording.

The nine isolated demo stations are WM-01, WS-01, DA-01, WB-04, MO-01, MK-01, TF-01, SG-01, and FT-01. A model or baseline for one machine or family is rejected for another.

The runtime intentionally represents one demonstration machine per family, keyed by family. It is not yet a general plant inventory for multiple simultaneous machines of the same family. The family-data stage may still learn from historical records for multiple real machines of one family.

This build does **not** provide calibrated failure probabilities, causal diagnosis, a real OSAT fleet validation, autonomous control, or a commercial SECS/GEM implementation. The model output is a `risk_score`, not a failure probability.

## Setup

Python 3.12 is the supported student environment.

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

The optional local LLM integration is isolated in `requirements-llm.txt`. Do not install it for the normal demo or tests.

The optional external benchmark parser is declared in
`requirements-benchmarks.txt`. The core pinned dependency file is unchanged.

## Run

```powershell
.venv\Scripts\python -m osat_edge.cli --help
.venv\Scripts\python -m osat_edge.cli demo
.venv\Scripts\python -m osat_edge.cli reference-replay
.venv\Scripts\python -m osat_edge.cli benchmark-nasa-milling --dataset benchmarks\_external\NASA_Milling.zip
.venv\Scripts\python -m osat_edge.cli evaluate-real --dataset kuka-kr3 --path benchmarks\_external\kuka-kr3
.venv\Scripts\python -m osat_edge.cli evaluate-real --all --root benchmarks\_external
.venv\Scripts\python -m osat_edge.cli ui
```

The deterministic demo initializes all nine stations and injects a synthetic WS-01 spindle fault. Any resulting ticket is plainly marked demo-only.

`reference-replay` runs the one bundled, checksum-verified
`SYNTHETIC + REAL_REPLAY` artifact through the actual telemetry, physics,
exact-machine, health, evidence, and deterministic demo-ticket path. See
[docs/REFERENCE_REPLAY.md](docs/REFERENCE_REPLAY.md).

`benchmark-nasa-milling` reads a user-supplied official NASA/UC Berkeley
Milling artifact and performs descriptive per-run analysis only. The raw data
are not bundled or downloaded automatically. It never enters OSAT health,
model, ticket, or HMI paths. See
[docs/EXTERNAL_BENCHMARK.md](docs/EXTERNAL_BENCHMARK.md).

The bundled replay is not real data. The NASA data are real external machining
data, but not semiconductor or OSAT data. Neither path is plant validation,
production qualification, or evidence of failure-prediction performance.

`evaluate-real` never downloads data, enters the operational pipeline, fits a
Step-05 family model, or calls Step 15. External inputs remain
`DataOrigin.EXTERNAL_BENCHMARK`; reports are written under
`.artifacts/real_data/` only with `--report`. See
[docs/REAL_DATA_CATALOG.md](docs/REAL_DATA_CATALOG.md) for source provenance,
exact mappings, attempted datasets, supported metrics, and limitations.

## HMI screens

- **FLEET** is the nine-station situational overview.
- **MACHINE** shows every approved canonical telemetry channel, one raw trend,
  exact-machine/family-model status, and subsystem evidence.
- **PHYSICS** exposes Step-01 runtime, research-only, and rejected relations,
  including maturity, limitations, uncertainty, falsification, and next experiments.
- **MAINTENANCE** separates deterministic evidence from optional retrieved/LLM prose.
- **SYSTEM** states runtime, telemetry-security, authority, network, and proprietary boundaries.

Phosphor amber is the neutral baseline; bright yellow, orange, and red are
reserved for abnormal conditions. State text accompanies every state color.
The design is informed by ISA-101 HMI principles, ISA-18 alarm-display
principles, NIST OT-security transparency guidance, and accessibility/contrast
guidance. This is design guidance, not a claim of conformance or certification.

## Verify

```powershell
.venv\Scripts\python -W error::ResourceWarning -m unittest discover -s tests -v
.venv\Scripts\python -m compileall osat_edge
```

Start with [docs/STUDENT_GUIDE.md](docs/STUDENT_GUIDE.md), then read the numbered modules in `osat_edge/roadmap/`.
