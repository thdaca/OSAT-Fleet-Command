# POST05: full functional proof of concept, 0.2.6 Snapshot 2

This is a system-integration proof using project-authored synthetic telemetry,
not new ML research, REAL_OSAT validation, prospective plant validation or
production qualification. Every report explicitly sets all three validation
flags false. Frozen equations, fitting, thresholds, station definitions,
fault logic and reference replay are not altered.

## One command and two dependency profiles

From the project root, with the root pinned runtime requirements installed:

```powershell
python -m osat_edge.ui.cli poc
```

Operational scenarios run without research tools, a network service, a model
server, llama.cpp or a GGUF. The additional local protocol profile is:

```powershell
python -m pip install -r osat_edge/roadmap/post_steps/post05_full_poc/resources/requirements-poc-simulator.txt
python -m osat_edge.ui.cli poc --require-connectivity
```

Without the optional dependency, the connectivity component is explicitly
`NOT_RUN_OPTIONAL_DEPENDENCY_ABSENT` and overall qualification is incomplete,
never PASS. `--require-connectivity` also returns a nonzero exit status then.
No external datasets are loaded by this command. No downloads occur at runtime.

The default report is `.artifacts/poc/0.2.6-poc.json`. It contains no wall-clock
run time, absolute machine paths, process IDs or ephemeral TCP ports. Two runs
under the same pinned profile must produce identical bytes and report hashes.
The committed `resources/0.2.6-poc.json` is the deterministic qualification
record, not a serialized operational model or a runtime database.

The report separates `functional_proof` (onboarding, monitoring, DecisionTrace,
model/ticket reload, retrieval and UNKNOWN scenarios) from
`external_scientific_evidence` (frozen executed POST04 results and lineage).
The headless command does not launch the UI; separate offscreen UI tests check
the operator screens. Neither section grants real OSAT or production validation.

Use `--artifacts .artifacts/poc-inspection-1` to retain one run's generated
model, nominal lineage and SQLite files. The directory must be new and strictly
inside `.artifacts`; repeat runs never reuse an earlier database. Without that
option an isolated temporary workspace is cleaned after each run.

## Ownership and sequence

`poc.py` only coordinates:

1. `scenarios/onboarding.py`: PRE02 WS-01 identity, POST01's existing synthetic
   source, Step08 atomic ingestion, Step01/03 parameter fitting, Step02/03
   features, Step06 nominal intervals and Step07 exact-machine fitting.
2. `scenarios/operational.py`: existing `MachinePipeline` calls for monitoring,
   anomaly/recovery, context shift, bad evidence and tickets. A cold pipeline
   has valid telemetry but no calibration/model and is UNKNOWN.
3. `scenarios/restart_probe.py`: new OS process loads the model and existing
   SQLite ticket, then runs the same pipeline and input sequence.
4. `scenarios/enrichment.py`: existing Steps11b–14 retrieve an authored document,
   exercise no-LLM fallback and valid/invalid JSON fixtures **after** a
   deterministic ticket exists. A valid fixture is not claimed as an LLM run.
5. `scenarios/connectivity.py`: optional fixed loopback HSMS session exercises
   the existing Step08 mapping and live invalid-batch handler.
6. `trace.py` and `reporting.py`: read decisions after inference and
   qualify them; they never influence health, scores, thresholds or tickets.

The source uses nine-family canonical definitions but the operational PoC is
deliberately one exact machine, `POC-WS-01` / `wafer_saw` / `WS-01`. A family
model remains optional/advisory and is not fitted or substituted for it.

## Nominal evidence and validation

All operational inputs have `DataOrigin.SYNTHETIC`. Their designation is
`POC_DESIGNATED_NOMINAL_SYNTHETIC_NOT_INDEPENDENT_PLANT_HEALTH`. The existing
Step06 API calls its interval `confirmed_healthy`; this API name and existing
Step10 wording are not independent evidence that a plant machine was healthy.

Onboarding collects 130 ticks for applicable existing physics fitting, then
35 feature rows for Step07 fitting. It purges 61 ticks before 35 disjoint
validation windows. Validation requires available unchanged Step07 output and
every health-eligible deviation below the **existing** WATCH entry threshold.
This is a functional acceptance criterion for an authored nominal scenario,
not a calibrated detector or independent failure test. Held-out bytes and
outputs have separate hashes. Monitoring starts after the nominal-history
interval and uses a fresh stream; no training window enters monitoring.

The spindle stimulus increases only POST01's existing input strength by
`0.000003` each tick for 150 ticks. It is not a score injection or threshold
change. Existing Step01 physical residuals and Step07 deviations drive frozen
Step09 NORMAL → WATCH → DEGRADED → CRITICAL and Step10 spindle localization.
Existing Step15 creates one HIGH demo ticket, then escalates that same ID to
URGENT. Recovery follows CRITICAL → DEGRADED → WATCH → NORMAL; the ticket stays
OPEN. The unsupported but legitimate IDLE context returns UNKNOWN instead of
being labeled a fault. This does not claim a validated model for every context.

Required missing/stale evidence returns UNKNOWN. A malformed live batch with
an unapproved source ID is rejected atomically: public store contents unchanged,
telemetry INVALID, health UNKNOWN, and the next valid batch is still processed.
Connectivity loss records last-known NORMAL separately from currently UNKNOWN.

## MODEL + TICKET RELOAD WITH DETERMINISTIC REPLAY

A fresh process loads the saved exact-machine model and existing SQLite ticket,
then replays the same healthy and progressive-deviation inputs through
`MachinePipeline`. The proof compares model identity, Step07 output, final
health, ticket ID, priority and OPEN status. Step09 starts fresh; this does
not demonstrate continuation of an arbitrary live hysteresis state.

## Minimal Step07 artifact contract

`step07_machine_model/model_io.py` supplies `save_machine_model()` and
`load_machine_model()`. Step07 fitting/evaluation math is unchanged; snapshot 1 behavior tests protect it.
There is no pickle, registry, plugin, migration, server or backward compatibility.

Schema `OSAT_EXACT_MACHINE_MODEL_V1` stores software version, exact machine ID,
family/station, origin, source/calibration/validation SHA-256 identities,
ordered feature/subsystem/kind contracts by operating context, fitted
centers/scales, physics parameters and their identity, and
`ACCEPTED_RESEARCH_ONLY` validation status. The envelope contains
`artifact_sha256` of canonical UTF-8 JSON payload bytes, sorted keys, compact
separators, finite numbers only, plus a trailing newline; its own digest field
is excluded. This differs intentionally from the SHA-256 of the full file.

Load requires caller-owned expected source/calibration/validation/physics and
feature identities. It rejects corruption, duplicate JSON keys, wrong machine,
family/station, version/schema, contracts, invalid scales/numbers, unvalidated
status and external-benchmark operational models. Synthetic artifacts cannot
be loaded for LIVE_EQUIPMENT. Saving verifies a temporary file before atomic
replacement. A hash is not a signature or protection against an attacker who
can replace both artifact and trusted expectations; it does not certify data.
POST05 leaves the model absent and reports UNKNOWN after a rejected load.

## SHADOW and LOOPBACK CONNECTIVITY PROOF

The shared PRE01 SHADOW contract explicitly allows ingestion, assessment,
fault evidence and recommendations/tickets **subject to the existing ticket
policy**. It fails closed on equipment commands, shutdown, recipe changes,
process control and unknown actions. It does not grant LIVE_EQUIPMENT or
external benchmarks ticket authority. CLI and dashboard show SHADOW / READ-ONLY.

The optional simulator uses secsgem codecs over local TCP with bounded reads,
timeouts, Select.req/Select.rsp and S6F11/S6F12. Fixture CEID 101 and authored
RPTID-to-SVID identities have no OEM significance. Only approved source IDs
reach normalization; malformed or unmapped reports enter the existing INVALID
handler. SemiGuard sends only Select.rsp and report receipt acknowledgments,
not equipment-control commands. All sockets bind/connect to 127.0.0.1 and close
after the run. No simulator logs or third-party source are bundled.

Dependency inventory: [secsgem 0.3.0](https://pypi.org/project/secsgem/0.3.0/),
release tag `v0.3.0`, **LGPL-2.1-or-later**, optional simulator only. Published
wheel SHA-256: `e1b89d5d47239de86d9da9d103736a7a86b57d28746f166dca88348f1776f960`.
The installed package's copyright header permits LGPL version 2.1 or later;
its code is imported as a separate dependency, never copied into runtime code.
See the upstream [HSMS API](https://secsgem.readthedocs.io/en/stable/reference/hsms.html).
This fixed local session is not full GEM negotiation, commercial protocol
qualification, equipment-control capability or evidence of OEM/plant interoperability.

## Frozen external evidence and release checks

`resources/frozen_025_science.json` retains the 112 original release-file hashes
from 0.2.5 Snapshot 6. `resources/frozen_025_sources.zip` preserves those bytes
without making legacy source active. Snapshot 2 reorganizes current modules;
`resources/snapshot2_implementation.json` pins their separate current identity.
POST05 rejects historical corruption and unapproved current-source drift
independently. Snapshot 1 behavior comparisons and POST04 science reproduction
verify behavior; a source digest alone does not prove equivalence.

POST04 experiment versions remain 0.2.5 independently of software VERSION
0.2.6. Its verifier checks immutable historical bytes and the entire freshly
reproduced scientific report, while reporting the **current** evaluator source
hash separately from the frozen evaluator hash. No metric, source identity,
split or threshold probe is relabeled. POST05 summarizes D2-led ST-AWFD support,
fragile D1 corroboration, TUHH descriptive evidence and other dataset statuses.
Those external datasets never enter the WS-01 model, health or ticket path.
The release-corrected reproducer is itself pinned in POST04's
`resources/0.2.6-reproducer.json`; unexpected source drift still fails closed.

```powershell
python -m compileall osat_edge
python -W error -m unittest discover -s osat_edge -t . -p "test_*.py" -v
python -W error -m unittest discover -s osat_edge/ui/tests -t . -v
python osat_edge/roadmap/steps/step01_physics_library/resources/run_physics_research_audit.py
python -m osat_edge.ui.cli demo
python -m osat_edge.ui.cli reference-replay
python -m osat_edge.ui.cli verify-real-evidence
python -m osat_edge.ui.cli poc --require-connectivity
python osat_edge/roadmap/pre_steps/pre01_common/resources/build_release.py
```

External reproduction requires separately obtained local pinned datasets;
root runtime tests do not download them. Clean releases include the authored
qualification record, but exclude environments, caches, raw external data,
generated models/nominal history, SQLite files and simulator output.
