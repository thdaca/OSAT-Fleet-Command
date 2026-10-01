# 0.2.6 Snapshot 2: contributor-focused restructuring

## What changed

- PRE01–PRE03, STEP01–STEP15 and POST01–POST05 retain their numbered directories
  and conceptual purposes. Implementation modules have direct names such as
  `contracts.py`, `features.py`, `model.py`, `health.py` and `tickets.py`.
- Step08 separates sources, atomic per-channel storage/quality and fail-closed
  SECS/GEM mapping. POST02 separates artifact validation from operational replay.
  Callers import functions from their actual owners.
- The dashboard window handles selection, timers and controls. Five ordinary
  QWidget screen classes own their widgets and presentation. Styles and shared
  widgets have clear homes, without forwarding proxies or mixins.
- POST03/POST04 share research metrics. Step07 shares its exact-machine identity
  check. POST04 removes redundant exports; reporting, lifecycle and dataset
  helpers are imported directly from their owners.
- The operational tick has readable ingestion, model-analysis, health/evidence
  and maintenance sections. Deterministic fallback precedes optional LLM wording
  with the same ticket authority and error behavior.
- Beginner, team, stage and screen guides explain inputs, outputs, owners,
  tests and first contributions. [The module map](MODULE_MAP.md) explains import
  changes. CLI commands and dependency pins remain unchanged.
- Original scientific sources and evidence retain their bytes separately from
  current implementation identity. [Release guidance](RELEASES.md) explains the
  historical source ZIP, which is never an active compatibility implementation.

## Scope of simplification

The longest source file falls from 1,261 lines to 649. The former monolithic
dashboard is divided by screen responsibility. Duplicated mathematical code,
identity checks, export lists and singleton `core/` indirection are removed.

Screen boundaries and separate historical/current integrity verification add
modules. Total active runtime/research source is approximately unchanged:
12,344 lines before and 12,465 after. Scientific metadata, validators, bounded
parsers, provenance schemes and frozen evidence remain because they carry
functionality and reproducibility requirements. The compressed historical
source bundle also makes the release ZIP larger.

## Validation

- The working tree initially matched every snapshot 1 archive member.
- The baseline suite ran 312 tests with one optional NASA environment-variable
  integration skip. A log initially triggered root cleanliness; moving it into
  `.artifacts/` and rerunning that check passed.
- Fixed observations captured before editing match snapshot 2 exactly: all
  fields of 185 nine-machine fleet ticks across normal/fault/recovery, complete
  demo and reference-replay payloads, PoC decisions, and 27 dashboard views
  across all nine families in healthy/faulted/disconnected states.
- The final ResourceWarning-strict suite runs 319 tests successfully, including
  seven added parity/source-drift checks. Its one optional direct NASA integration
  test is also run separately against the locally supplied official ZIP.
- The full PoC qualifies PASS, including optional loopback connectivity, UNKNOWN
  cases, fault localization, persistent/escalated tickets, process restart and
  deterministic enrichment fallback.
- POST04 verifies all 13 frozen dataset entries and the complete aggregate
  scientific report, preserves historical 0.2.4 bytes and reports zero operational
  tickets. Frozen 0.2.5 evidence and all 112 archived baseline files remain intact.
- The release builder checks member paths, duplicates, excluded local/runtime
  files and CRCs. Fresh-extraction checks cover commands, PoC, source imports and
  the complete suite: 319 tests, with five expected optional-data skips because
  raw external datasets are excluded. The source-tree suite and separate NASA
  check cover these paths with locally supplied data. Source compiles and local
  Markdown targets resolve.

These checks establish behavior preservation for the existing test/scenario
coverage. They do not establish REAL_OSAT validation, causal diagnosis,
prospective plant performance, OEM interoperability or production qualification.
