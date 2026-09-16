# OSAT Fleet Command 0.2.0

**RESEARCH / DEVELOPMENT BUILD — not production qualified**

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
9. deterministic simulation-only maintenance ticket;
10. optional local manual retrieval and local-LLM wording.

The nine isolated demo stations are WM-01, WS-01, DA-01, WB-04, MO-01, MK-01, TF-01, SG-01, and FT-01. A model or baseline for one machine or family is rejected for another.

The 0.2.0 runtime intentionally represents one demonstration machine per family, keyed by family. It is not yet a general plant inventory for multiple simultaneous machines of the same family. The family-data stage may still learn from historical records for multiple real machines of one family.

This build does **not** provide calibrated failure probabilities, causal diagnosis, a real OSAT fleet validation, autonomous control, or a commercial SECS/GEM implementation. The model output is a `risk_score`, not a failure probability.

## Setup

Python 3.12 is the supported student environment.

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

The optional local LLM integration is isolated in `requirements-llm.txt`. Do not install it for the normal demo or tests.

## Run

```powershell
.venv\Scripts\python -m osat_edge.cli --help
.venv\Scripts\python -m osat_edge.cli demo
.venv\Scripts\python -m osat_edge.cli ui
```

The deterministic demo initializes all nine stations and injects a synthetic WS-01 spindle fault. Any resulting ticket is plainly marked demo-only.

## Verify

```powershell
.venv\Scripts\python -W error::ResourceWarning -m unittest discover -s tests -v
.venv\Scripts\python -m compileall osat_edge
```

Start with [docs/STUDENT_GUIDE.md](docs/STUDENT_GUIDE.md), then read the numbered modules in `osat_edge/roadmap/`.
