# Student guide

OSAT Fleet Command 0.2.5 is intentionally a minimum research build with a
transparent industrial edge-monitoring HMI prototype. Start with
`osat_edge/roadmap/README.md`; the file names are the architecture map.

## The path through the code

- `roadmap/pre_steps/pre01_common/pre01_common.py` contains shared identities, modes, states,
  and telemetry contracts.
- `roadmap/pre_steps/pre02_machine_registry/pre02_machine_registry.py` is the sole registry of the nine
  station families and their explicitly approved channels.
- `roadmap/pre_steps/pre03_data_provenance/pre03_data_provenance.py` verifies external source bytes,
  REAL_OSAT origin claims, label semantics, and optional canonical mappings.
- `roadmap/steps/step01` through `step03` turn reviewed engineering
  relationships and robust telemetry statistics into evidence.
- `roadmap/steps/step04` through `step07` keep same-family learning separate
  from the baseline for one installed machine.
- `roadmap/steps/step08` through `step10` ingest asynchronous telemetry and
  produce subsystem-first health and structured fault evidence.
- `roadmap/steps/step11a` through `step15` persist deterministic tickets and
  isolate optional retrieval/LLM wording behind strict validation.
- `pipeline.py` connects those steps with explicit control flow.
- `roadmap/post_steps/post01_demo/post01_demo.py` owns synthetic generation and injection;
  POST02 validates the frozen synthetic replay, POST03 runs the isolated NASA
  description, and POST04 evaluates explicitly supplied external data offline.
- `ui/cli.py` and `ui/dashboard.py` are human interfaces, not roadmap stages.

## Boundaries to preserve

Data quality asks whether telemetry is valid. Observability asks whether enough useful telemetry exists. Health asks what condition the evidence supports. They are related but not interchangeable.

Synthetic data can test and demonstrate the architecture. It is not real OSAT
evidence. Runtime mode says how code executes; data origin says what the
evidence is. The reference fixture therefore uses `REAL_REPLAY` execution with
`SYNTHETIC` origin. LIVE_EQUIPMENT and REAL_OSAT replay are observe-only in this
release; they cannot create actionable tickets. The optional RAG/LLM branch can
only improve wording after deterministic evidence exists.

PRE03 accepts canonical REAL_OSAT directory identities only through the
unambiguous `CANONICAL_FILE_SET_SHA256_V2` scheme. Legacy directory hashing is
retained solely to reproduce already-committed external benchmark evidence.

The live/demo runtime is deliberately one machine per family. Its `machines[family]` mapping is not a general plant inventory for WS-01, WS-02, and WS-03 at the same time. This does not prevent the family-data stage from learning across historical records from multiple machines of that family.

Read the POST02 `post02_reference_replay/research/REFERENCE_REPLAY.md`
before changing the bundled fixture. Read the POST03
`post03_external_benchmark/research/EXTERNAL_BENCHMARK.md` before analyzing
the optional NASA data. External machining observations are not OSAT evidence,
and the benchmark is intentionally prevented from producing health states or
maintenance tickets.

Read the POST04 `post04_real_data_evaluation/research/REAL_DATA_CATALOG.md`
before using `evaluate-real`.
External data are offline research inputs only; a semantically similar signal
is not automatically an approved OSAT channel. A compatible file is also not
automatically the official real dataset: pinned archive/content identity must
match before `real_data=true` is emitted.

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

Run the full suite with `python -W error::ResourceWarning -m unittest discover
-s osat_edge -t . -p "test_*.py" -v`, inspect one stage with its colocated
tests, make one narrow change, run that test file, and then run the full suite.
Avoid introducing general frameworks for a requirement that appears only once.
