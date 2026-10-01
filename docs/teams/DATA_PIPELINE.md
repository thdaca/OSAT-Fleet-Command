# Data Pipeline & Systems Integration

**Does the whole pipeline parse, process and deliver data correctly and
consistently, so every team can trust its inputs and outputs?**

## Entry files

- [PRE01 contracts](../../osat_edge/roadmap/pre_steps/pre01_common/contracts.py):
  identities, origins, timestamps and immutable channel windows.
- [PRE02 registry](../../osat_edge/roadmap/pre_steps/pre02_machine_registry/registry.py):
  the sole approved station/channel definitions.
- [PRE03 provenance](../../osat_edge/roadmap/pre_steps/pre03_data_provenance/provenance.py):
  source identities, label semantics and REAL_OSAT mappings.
- [Step08 sources](../../osat_edge/roadmap/steps/step08_live_telemetry/sources.py):
  batches, bounded live queue and historical replay.
- [Step08 store](../../osat_edge/roadmap/steps/step08_live_telemetry/store.py):
  atomic ingestion, bounded history, quality and observability.
- [Step08 SECS/GEM](../../osat_edge/roadmap/steps/step08_live_telemetry/secs_gem.py):
  approved S6F11 mappings and rejected unknown/process-IP fields.
- [Pipeline](../../osat_edge/pipeline.py): explicit end-to-end orchestration.
- [POST05 PoC](../../osat_edge/roadmap/post_steps/post05_full_poc/poc.py) and
  [scenarios](../../osat_edge/roadmap/post_steps/post05_full_poc/scenarios/):
  full-system functional checks, including uncertainty, restart and connectivity.

Start with `append_batch` and [telemetry tests](../../osat_edge/roadmap/steps/step08_live_telemetry/tests/test_step08_telemetry.py),
then [provenance tests](../../osat_edge/roadmap/pre_steps/pre03_data_provenance/tests/test_pre03_data_provenance.py).

## What this team owns

Own integration and consistency across the full PRE / STEP / POST flow: input
parsing, validation, storage, analysis connections, result delivery and the
interfaces used by UI and research checks. A clean input reader is only one part
of the responsibility. Follow a sample through the entire pipeline and ensure
identity, timing, units, context, source origin and evidence meaning remain intact.

Receive measurement requirements and semantics from Failure Research. Agree on
source IDs, units, machine identity, timestamps, sampling period, staleness and
availability before sending signals to ML. Return usable windows, context,
provenance and rejection reasons. Integrate ML's algorithm through the existing
pipeline, and deliver consistent results to Reliability and UI.

## Whole-system validation

Check that components work together, results reach the correct machine and
consumer, malformed or unavailable data is handled correctly, and storage,
replay, restart and connectivity respect their documented contracts. Use existing
end-to-end scenarios and regression tests as evidence; do not mistake a component
test for complete system coverage. Coordinate with stage owners when a shared
contract changes.

This team's functional question is whether the system processes and routes data
correctly. Reliability's statistical question is whether the resulting conclusions
are supported by honest evidence. Both examine the whole pipeline and collaborate;
neither check replaces the other. A passing synthetic integration test does not
qualify a plant detector.

A first contribution can document one sample's path through input, features,
model, health and display, including an invalid-input path. For a future code
version, a bounded integration test can protect that path. The 0.2.6 application
and tests remain frozen.

Do not silently rename external columns into OSAT channels or assume synchronized
rows. Keep machines separate and preserve whole-batch rejection. Recipes, PPIDs,
wafer maps, geometry and unapproved variables cannot be ingested. Rejected live
input becomes invalid/UNKNOWN without reusing a cached NORMAL claim.
