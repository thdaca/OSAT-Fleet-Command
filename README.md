# OSAT SemiGuard — 0.2.6 (Snapshot 2)

**OSAT SemiGuard** is a controlled end-to-end proof of concept for
semiconductor equipment-health evidence. Health is deterministic;
optional language models only add ticket wording. It is not production qualified.

Every release includes `OSAT_SemiGuard_Architecture.pdf` directly inside the ZIP's
project root. Its [editable architecture source](docs/ARCHITECTURE_GUIDE.md) and
[cumulative changelog](docs/CHANGELOG.md) begin at 0.2.6. Follow the
[PDF release workflow](docs/PDF_RELEASE_WORKFLOW.md) for future changes.

Start with [STUDENT_GUIDE.md](STUDENT_GUIDE.md), then choose [your team](docs/teams/README.md).
Read [how data moves](docs/ARCHITECTURE.md), [evidence boundaries](docs/EVIDENCE.md)
and [the complete stage map](osat_edge/roadmap/README.md) as needed.

## Architecture and folders

```text
PRE-STEPS                  STEPS                         POST-STEPS
identity, channels,  →     physics, features, models, →   demo, replay,
provenance                 health, evidence, tickets     research, functional PoC

osat_edge/
  pipeline.py             explicit operational orchestration
  roadmap/pre_steps/      PRE01–PRE03 trust contracts
  roadmap/steps/          STEP01–STEP15 analysis and maintenance
  roadmap/post_steps/     POST01–POST05 demonstration and research
  ui/cli.py              headless commands
  ui/dashboard.py        window, selection, timers and controls
  ui/screens/            five separately owned screens
  ui/widgets.py          trends, cards, tables and display formatting
  ui/theme.py            colors and styles
docs/                    architecture, evidence and five team entry guides
.artifacts/              ignored generated outputs
benchmarks/_external/    ignored user-supplied external datasets
```

Stage numbering identifies responsibility. Training and monitoring use different
parts of this architecture. Snapshot 2 shortens implementation names, separates
telemetry and screen ownership, consolidates duplicate calculations and adds
beginner/team guides. See [changes and validation](docs/SNAPSHOT_2.md).

## Setup and run

Python 3.12 is the supported environment. From this README's directory:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m osat_edge.ui.cli demo
.venv\Scripts\python -m osat_edge.ui.cli ui
```

The demo initializes nine isolated stations and injects an authored WS-01 spindle
fault. The dashboard retains FLEET, MACHINE, PHYSICS, MAINTENANCE and SYSTEM,
including uncertainty, UNKNOWN, provenance and current/last-known evidence.

## Other commands

```powershell
.venv\Scripts\python -m osat_edge.ui.cli --help
.venv\Scripts\python -m osat_edge.ui.cli reference-replay
.venv\Scripts\python -m osat_edge.ui.cli poc
.venv\Scripts\python -m osat_edge.ui.cli benchmark-nasa-milling --dataset benchmarks\_external\NASA_Milling.zip
.venv\Scripts\python -m osat_edge.ui.cli evaluate-real --dataset kuka-kr3 --path benchmarks\_external\kuka-kr3
.venv\Scripts\python -m osat_edge.ui.cli evaluate-real --all --root benchmarks\_external --report
.venv\Scripts\python -m osat_edge.ui.cli verify-real-evidence --root benchmarks\_external
```

The reference replay is checksum-verified **synthetic** evidence. Replay execution
does not make it real OSAT data. External commands stay outside operational health
and ticket authority and never download inputs. Raw external datasets are excluded
from snapshots. Historical 0.2.4/0.2.5 evidence retains its original identity.

The PoC requires no GGUF. To include optional loopback HSMS connectivity:

```powershell
.venv\Scripts\python -m pip install -r osat_edge\roadmap\post_steps\post05_full_poc\resources\requirements-poc-simulator.txt
.venv\Scripts\python -m osat_edge.ui.cli poc --require-connectivity
```

Without that dependency, connectivity is explicitly NOT_RUN and qualification
incomplete. The report defaults to `.artifacts/poc/0.2.6-poc.json`. Optional LLM,
physics-audit, benchmark and surface-parser requirements remain stage-owned;
they are not added to core requirements. Stage READMEs link reproducibility notes.

## Verify

```powershell
.venv\Scripts\python -W error::ResourceWarning -m unittest discover -s osat_edge -t . -p "test_*.py" -v
.venv\Scripts\python -m compileall -q osat_edge
```

[Contributing](docs/CONTRIBUTING.md) explains targeted checks and release pins.
The runtime represents one demonstration machine per family, keyed by family,
not several simultaneous installed machines of the same family. Family training
can use multiple historical machines. LIVE_EQUIPMENT and REAL_OSAT replay remain
observe-only. Risk scores are not failure probabilities. No equipment control,
causal diagnosis, prospective plant validation or autonomous closure is provided.
