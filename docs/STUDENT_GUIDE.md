# Student guide

OSAT Fleet Command 0.2.4 is intentionally a minimum research build with a
transparent industrial edge-monitoring HMI prototype. Read it from `step01` to
`step15`; the file names are the architecture map.

## The path through the code

- `common.py` contains only shared identities, modes, states, and telemetry contracts.
- `machines.py` lists the nine machine families and the explicitly approved channels for each.
- `roadmap/step01` through `step03` turn reviewed engineering relationships and robust telemetry statistics into evidence.
- `roadmap/step04` and `step05` define optional learning across real machines of one family. The output is a risk score.
- `roadmap/step06` and `step07` build a separate baseline for one installed machine using confirmed healthy history.
- `roadmap/step08` ingests asynchronous per-channel telemetry, enforces approved source IDs, and reports validity and observability.
- `roadmap/step09` makes subsystem-first deterministic health decisions with fixed hysteresis.
- `roadmap/step10` creates compact structured fault evidence.
- `roadmap/step11a` stores tickets in SQLite. `step11b` loads local reviewed manual/playbook passages.
- `roadmap/step12` retrieves only relevant local context. `step13` optionally calls a local GGUF model. `step14` strictly validates its small JSON response.
- `roadmap/step15` creates or updates a deterministic ticket. It refuses to do so outside simulation.
- `pipeline.py` connects those steps with explicit control flow. `demo.py` owns
  live synthetic generation and injection. `reference_replay.py` validates and
  runs the one frozen synthetic replay artifact. `benchmark.py` is a separate,
  descriptive external-data analysis path. `real_data.py` is the isolated
  offline evaluator for explicitly supplied external real data.

## Boundaries to preserve

Data quality asks whether telemetry is valid. Observability asks whether enough useful telemetry exists. Health asks what condition the evidence supports. They are related but not interchangeable.

Synthetic data can test and demonstrate the architecture. It is not real OSAT
evidence. Runtime mode says how code executes; data origin says what the
evidence is. The reference fixture therefore uses `REAL_REPLAY` execution with
`SYNTHETIC` origin. LIVE_EQUIPMENT and REAL_OSAT replay are observe-only in this
release; they cannot create actionable tickets. The optional RAG/LLM branch can
only improve wording after deterministic evidence exists.

The live/demo runtime is deliberately one machine per family. Its `machines[family]` mapping is not a general plant inventory for WS-01, WS-02, and WS-03 at the same time. This does not prevent the family-data stage from learning across historical records from multiple machines of that family.

Read [REFERENCE_REPLAY.md](REFERENCE_REPLAY.md) before changing the bundled
fixture. Read [EXTERNAL_BENCHMARK.md](EXTERNAL_BENCHMARK.md) before analyzing
the optional NASA data. External machining observations are not OSAT evidence,
and the benchmark is intentionally prevented from producing health states or
maintenance tickets.

Read [REAL_DATA_CATALOG.md](REAL_DATA_CATALOG.md) before using `evaluate-real`.
External data are offline research inputs only; a semantically similar signal
is not automatically an approved OSAT channel.

Source identifiers must be explicitly reviewed and mapped to canonical health channels. Do not ingest recipes, PPIDs, wafer maps, geometry, proprietary process windows, or unknown equipment variables.

## Reading the HMI

Use **FLEET** for situational awareness, **MACHINE** for current telemetry and
subsystem evidence, **PHYSICS** for Step-01 credibility and rejected-relation
research, **MAINTENANCE** for downstream tickets, and **SYSTEM** for runtime,
security, and authority facts. Phosphor amber is neutral; strong colors identify
abnormal conditions, always with explicit text. The design is informed by
industrial HMI, alarm-display, OT-security, and accessibility guidance; it has
not undergone a formal conformance assessment.

## Safe first contribution

Run the full suite, inspect one numbered step with its matching tests, make one narrow change, run that test file, and then run the full suite. Avoid introducing general frameworks for a requirement that appears only once.
