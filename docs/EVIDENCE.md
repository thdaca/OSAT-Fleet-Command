# Evidence, uncertainty and authority

Keep three questions separate: can the data be trusted, what conclusion does
the evidence support, and what action does this runtime authorize?

## Data and provenance

Quality checks identities, approved source IDs, units, finite values, ordering
and freshness. Observability checks whether enough current usable telemetry
and equipment-state context exist. Valid data without a calibrated exact-machine
context still cannot support a health claim.

UNKNOWN means a supported health classification is unavailable. It is distinct
from NORMAL, WATCH, DEGRADED and CRITICAL. Missing inputs, stale context,
unavailable models and rejected live batches must not become NORMAL.

RuntimeMode describes SIMULATION, REAL_REPLAY or LIVE_EQUIPMENT execution.
DataOrigin describes SYNTHETIC, EXTERNAL_BENCHMARK or REAL_OSAT evidence.
The bundled reference is SYNTHETIC with REAL_REPLAY mode.

PRE03 verifies source bytes, channel mappings and label semantics before a
REAL_OSAT declaration. Its canonical directory scheme is
CANONICAL_FILE_SET_SHA256_V2; legacy hashing only reproduces historical external
evidence. A similar column name does not authorize an OSAT channel. Compatible
local files require pinned source identity before being called official real data.

Exact-machine models must match machine ID, family and station. Family models
cannot cross families. Healthy feature windows must fit entirely within
confirmed-healthy intervals. These safeguards are essential complexity.

## Research conclusions

Failure Research records mechanisms, measurement requirements, confounders,
references, uncertainty and falsification criteria. Step01 keeps runtime,
research-only and rejected relationships visible.

Reliability checks held-out evidence and returns **SUPPORTED**, **REVISE**,
**COLLECT MORE DATA** or **ABSTAIN** with scope and limitations. These are human
handoff outcomes, not a new automatic gate implemented in this release.
Discrimination, threshold transfer, calibration and temporal performance are
different claims. A good ranking metric does not validate operational thresholds.
An anomaly does not prove a physical cause; risk scores are not probabilities.

POST04 datasets retain EXTERNAL_BENCHMARK origin and cannot fit Step05 family
models or create operational health, fault evidence, tickets or HMI inputs.
Historical 0.2.4 and 0.2.5 evidence retain their original byte identities.

## Maintenance and equipment authority

SIMULATION and the checksum-verified bundled synthetic replay can create demo
tickets under the existing policy. LIVE_EQUIPMENT and REAL_OSAT replay remain
observe-only. Step15 accepts simulation evidence; the pipeline explicitly bridges
only the authorized synthetic reference replay. Never broaden that bridge to
arbitrary replays.

SHADOW forbids equipment commands, shutdowns, recipe changes and process control.
It does not expand ticket eligibility. Retrieval and the optional LLM can add
validated wording after deterministic evidence exists; they cannot decide health
or authorize tickets. UI must distinguish current from last-known evidence and
show uncertainty in text as well as color.
