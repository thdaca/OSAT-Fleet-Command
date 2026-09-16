# OSAT Fleet Command 0.2.5

**RESEARCH / DEVELOPMENT BUILD — not production qualified**

Release title: **STEP01 PHYSICS-LIBRARY FOUNDATION**

Version 0.2.5 modularizes the Step01 physics library and adds optional offline
unit, symbolic, and experiment-design audits. The 0.2.3 inference method,
thresholds, canonical stations, demo, reference replay, UI, security boundary,
ticket authority, and historical 0.2.4 deterministic evidence are not tuned,
redesigned, or relabeled.

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

The optional local LLM integration is isolated beside Step 13 at
`osat_edge/roadmap/steps/step13_local_llm/resources/requirements-llm.txt`.
Do not install it for the normal demo or tests.

The optional external benchmark parser is declared in
`osat_edge/roadmap/post_steps/post03_external_benchmark/resources/requirements-benchmarks.txt`.
The core pinned dependency file is unchanged.

The optional Step01 research-audit dependencies and command are isolated in
`osat_edge/roadmap/steps/step01_physics_library/resources/`:

```powershell
.venv\Scripts\python -m pip install -r osat_edge\roadmap\steps\step01_physics_library\resources\requirements-physics-research.txt
.venv\Scripts\python osat_edge\roadmap\steps\step01_physics_library\resources\run_physics_research_audit.py
```

They are not required for normal edge inference or the core test suite.

## Run

```powershell
.venv\Scripts\python -m osat_edge.ui.cli --help
.venv\Scripts\python -m osat_edge.ui.cli demo
.venv\Scripts\python -m osat_edge.ui.cli reference-replay
.venv\Scripts\python -m osat_edge.ui.cli benchmark-nasa-milling --dataset benchmarks\_external\NASA_Milling.zip
.venv\Scripts\python -m osat_edge.ui.cli evaluate-real --dataset kuka-kr3 --path benchmarks\_external\kuka-kr3
.venv\Scripts\python -m osat_edge.ui.cli evaluate-real --all --root benchmarks\_external
.venv\Scripts\python -m osat_edge.ui.cli ui
```

The deterministic demo initializes all nine stations and injects a synthetic WS-01 spindle fault. Any resulting ticket is plainly marked demo-only.

`reference-replay` runs the one bundled, checksum-verified
`SYNTHETIC + REAL_REPLAY` artifact through the actual telemetry, physics,
exact-machine, health, evidence, and deterministic demo-ticket path. See
[POST02 replay notes](osat_edge/roadmap/post_steps/post02_reference_replay/research/REFERENCE_REPLAY.md).

`benchmark-nasa-milling` reads a user-supplied official NASA/UC Berkeley
Milling artifact and performs descriptive per-run analysis only. The raw data
are not bundled or downloaded automatically. It never enters OSAT health,
model, ticket, or HMI paths. See
[POST03 benchmark notes](osat_edge/roadmap/post_steps/post03_external_benchmark/research/EXTERNAL_BENCHMARK.md).

The bundled replay is not real data. The NASA data are real external machining
data, but not semiconductor or OSAT data. Neither path is plant validation,
production qualification, or evidence of failure-prediction performance.

`evaluate-real` never downloads data, enters the operational pipeline, fits a
Step-05 family model, or calls Step 15. External inputs remain
`DataOrigin.EXTERNAL_BENCHMARK`. Compatible local bytes are declared real only
after a pinned official artifact/content identity matches. Runtime timings are
printed by the CLI but omitted from the deterministic report written under
`.artifacts/real_data/` only with `--report`. See
[POST04 real-data catalog](osat_edge/roadmap/post_steps/post04_real_data_evaluation/research/REAL_DATA_CATALOG.md)
for source provenance,
exact mappings, attempted datasets, supported metrics, and limitations.
When the official datasets are already present locally, `verify-real-evidence`
first checks the immutable historical `0.2.4-real-data.json` byte identity, then
separately re-runs the current datasets without network access and checks the
deterministic comparison against `0.2.5-real-data.json`. A current evaluator
hash is not compared with the historical evaluator hash.

POST04 is organized by explicit dataset owner under `datasets/`, with only
shared metrics, bounded reporting, and evidence lifecycle code under `core/`.
ST-AWFD reports material-scoring, headline-step, and complete-headline-material
coverage separately; continuous discrimination evidence is kept distinct from
unsupported transfer/calibration of the frozen Step09 thresholds. Third-party
data rights and the optional TUHH parser are recorded in
`post04_real_data_evaluation/resources/THIRD_PARTY_DATA_USE.json`. Raw external
datasets remain ignored and excluded from releases.

## Repository map

```text
osat_edge/
├── pipeline.py                         linear operational orchestrator
├── roadmap/
│   ├── pre_steps/                      PRE01 contracts, PRE02 registry, PRE03 provenance
│   ├── steps/                          STEP01–STEP15 PHM/maintenance path
│   └── post_steps/                     POST01 demo through POST04 evaluation
└── ui/                                 CLI and PyQt dashboard
```

The conceptual flow is **PRE-STEPS → STEPS 01–15 → POST-STEPS**. The UI is a
separate sibling interface. Each named stage has one folder containing its
same-named implementation module and any owned `research/`, `tests/`, or
`resources/` directories. See
[`osat_edge/roadmap/README.md`](osat_edge/roadmap/README.md).

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
.venv\Scripts\python -W error::ResourceWarning -m unittest discover -s osat_edge -t . -p "test_*.py" -v
.venv\Scripts\python -m compileall osat_edge
```

Start with [STUDENT_GUIDE.md](STUDENT_GUIDE.md), then follow
[the roadmap](osat_edge/roadmap/README.md).
