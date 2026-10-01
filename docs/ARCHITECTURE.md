# How data and evidence move

The architecture remains **PRE-STEPS → STEPS → POST-STEPS**. PRE-STEPS establish
trust contracts. STEPS implement analysis and maintenance. POST-STEPS exercise
the system and evaluate research. The UI is a sibling presentation layer.

## Before monitoring

PRE01 defines identities, timestamps, telemetry contracts, origins and modes.
PRE02 defines the nine approved station families and channels. PRE03 verifies
source identity, label semantics and any REAL_OSAT mapping.

Step01 separates approved runtime physics from research candidates and rejected
claims. A plausible paper or candidate alone does not grant runtime authority.
Steps04–05 optionally fit real-only same-family event risk with machine-isolation
checks. Steps06–07 fit a baseline for one exact machine from confirmed-healthy
windows, separated by equipment state. Training is preparation, not repeated
on every live sample.

## One monitoring tick

Start with `MachinePipeline.tick()` in [pipeline.py](../osat_edge/pipeline.py):

```text
STEP08 source.poll → atomic store → quality and observability
  ↓ independently timed usable channel windows
STEP02 median, spread and slope features
STEP03 timestamp-overlap physical residuals
STEP07 exact-machine deviations + optional STEP05 advisory family risk
  ↓ current evidence
STEP09 subsystem scores, persistence and hysteresis → health assessment
STEP10 structured fault evidence
  ↓ eligible transition plus existing runtime/origin policy
STEP11a prior tickets + STEP11b local manuals → STEP12 retrieval
STEP14 deterministic fallback → STEP15 demo ticket
STEP13 optional LLM → STEP14 validation → STEP15 optional wording update
  ↓
PipelineResult → UI and POST-STEP observations
```

Stage numbers identify responsibility, not a promise that every stage runs in
numeric order on every tick. Step08 supplies telemetry before Steps02–03 can
compute features. The deterministic ticket is saved before optional LLM wording.
The pipeline uses ordinary functions and dataclasses, without a stage scheduler
or implicit dependency injection.

## Follow an authored WS-01 spindle example

POST01 generates canonical `spindle_speed`, `spindle_current` and other signals
with their own periods. Step08 checks identity, units, source IDs and ordering,
then stores each channel separately. It rejects a malformed batch before
committing any sample. Step02 summarizes usable windows. Step03 aligns only
shared timestamp support and evaluates the spindle residual when its calibrated
domain and measurements permit it.

Step07 compares features with the exact-machine healthy reference. Step09 uses
eligible location/physics deviations, subsystem maxima and time persistence.
Family risk remains advisory. An eligible simulation transition can produce
structured fault evidence and one demo ticket; escalation updates that ticket.
Recovery does not close it. The display explains evidence without causal proof
or a failure probability. Read the tests in Steps03, 07, 08, 09 and 15 to follow
one boundary without first mastering the whole system.

## What POST-STEPS prove

- POST01 demonstrates nine isolated synthetic stations.
- POST02 validates the synthetic reference before operational replay. Expected
  checkpoints observe decisions; they never influence inference.
- POST03 describes user-supplied external NASA Milling data outside OSAT health.
- POST04 runs dataset-owned offline research. It can reuse pure model arithmetic
  without invoking operational health, fault or ticket stages.
- POST05 checks onboarding, monitoring, persistence, process restart and optional
  loopback connectivity. Its trace reads decisions after they happen.

Research findings never silently become equipment authority. See
[evidence boundaries](EVIDENCE.md) and [the stage map](../osat_edge/roadmap/README.md).
