# Reproduce and package a release

## Historical evidence and current sources

The original `0.2.4-real-data.json`, `0.2.5-real-data.json` and
`frozen_025_science.json` are immutable. POST05's `frozen_025_sources.zip` preserves
all 112 originally pinned files byte-for-byte, including scientific source and
research notes. The application never imports or extracts that archive. It is
historical provenance, not a second active implementation.

Snapshot 2 reorganizes current code. Its `snapshot2_implementation.json` records
a separate canonical source/input identity, and `0.2.6-reproducer.json` records
the current external evaluator identity. POST05 rejects historical corruption
and unreviewed current-source drift separately. Source hashing detects changes;
it does not prove behavior equivalence, valid measurements or authorization.

PRE01 resources contain fixed `snapshot1_behavior.json` observations captured
before editing snapshot 1. Its tests compare complete fleet results, demo/replay,
PoC decisions and 27 dashboard views. Only changing PoC release/lineage identities
and the UI wall clock are excluded. The official SemiGuard rename is normalized
only in display strings and the connectivity host-field name. Current report
sections are flattened for comparison; added scope wording is excluded. All
original decision/value digests remain fixed. Do not rewrite them to mask drift.

## Release maintainer workflow

1. Review the change against the original behavior tests and science assumptions.
   Run affected tests, the full suite and fixed snapshot 1 parity checks.
2. For evaluator changes, use the locally supplied official dataset root to
   reproduce the complete frozen external aggregate evidence. No downloads occur.
3. When an intentional source change needs new release identities, record the
   output of `post05_full_poc.lineage.implementation_identity()` in the current
   implementation pin, and `core.evidence_lifecycle.evaluator_source_sha256()`
   in the current reproducer pin. The modules are under `roadmap/post_steps/`.
   Review numerical comparisons before approving the pins. Historical hashes
   and evidence are never relabeled as new code.
4. Regenerate the current PoC report with the optional simulator installed, and
   verify it alongside the current pins. A missing simulator is explicitly
   incomplete; it is not a successful connectivity qualification.
5. Run final tests, then build and check the archive. Test an extracted copy
   using the same supported Python environment.

Ordinary contributors can run targeted tests while drafting. Source-drift checks
deliberately fail until current release identities are reviewed. Keep generated
outputs in `.artifacts/` and do not include raw third-party datasets or environments.

## Packaging command

From the repository root:

```powershell
.venv\Scripts\python -m osat_edge.roadmap.pre_steps.pre01_common.resources.build_release
```

The default output is `../snapshots/0.2.6 (snapshot 2).zip`. The builder includes
source, stage resources/tests and contributor documentation, excludes caches,
runtime databases, `.artifacts/`, environments and external datasets, and checks
unique portable member names and CRCs before replacing the destination.

The accepted snapshot archives remain historical records. The reviewed 0.2.6
PoC handoff uses `--output "../snapshots/0.2.6.zip"` to preserve snapshot 2's ZIP.

Every current/future release ZIP also requires the root-level architecture PDF.
Use [the documentation renderer and packaging step](PDF_RELEASE_WORKFLOW.md)
after the existing checks; the unchanged 0.2.6 builder alone does not include
that additional root file. Maintain the guide minimally and append each new
version to [the cumulative changelog](CHANGELOG.md).

The source bundle makes this ZIP larger than a source-only archive. It preserves
reproducibility without exposing legacy source as active modules. The active
implementation removes duplicated calculations and keeps the numbered architecture
intact. See the source-size and validation scope in [SNAPSHOT_2.md](SNAPSHOT_2.md).
