# Repository rules

OSAT SemiGuard 0.2.6 Snapshot 2 is a research/development student project.

- Start with STUDENT_GUIDE.md, docs/teams/README.md and the owning stage README.
- Import from each function's concrete owner; do not reintroduce old-path shims.
- UI screens own presentation only; pipeline.py connects operational stages.

- Keep PRE01–PRE03 in `osat_edge/roadmap/pre_steps/`, Step01–Step15 in
  `osat_edge/roadmap/steps/`, and POST01–POST05 in
  `osat_edge/roadmap/post_steps/`, aligned with the documented roadmap.
- Prefer explicit ordinary Python and small dataclasses over framework-like indirection.
- Preserve machine-family and exact-machine identity checks.
- Preserve asynchronous per-channel telemetry and fail-closed source-ID mapping.
- Keep synthetic evidence separate from real OSAT evidence.
- LIVE_EQUIPMENT and REAL_OSAT replay are observe-only. SIMULATION and the
  checksum-verified bundled SYNTHETIC reference replay may create demo-only
  maintenance tickets.
- Runtime mode and data origin are separate. Never infer REAL_OSAT from
  REAL_REPLAY.
- Keep the NASA Milling benchmark isolated from OSAT physics, models, health,
  tickets, and the HMI. It is external non-semiconductor machining data.
- Health is deterministic. RAG and the optional local LLM may enrich a ticket, never create it.
- POST05 orchestrates existing stages; traces never influence inference. SHADOW
  forbids equipment control and does not expand live/external ticket authority.
- Keep original 0.2.4/0.2.5 evidence and the preserved `frozen_025_sources.zip`
  source bytes intact. Current sources have a separate snapshot 2 identity pin;
  do not relabel changed implementation as historical bytes or refresh expected
  behavior digests to hide drift. See docs/RELEASES.md.
- Runtime model, SQLite, nominal-history and simulator artifacts belong under `.artifacts/`.
- Do not call a risk score a failure probability.
- Do not add compatibility layers for deleted pre-0.2.0 architecture.
- Run `python -W error::ResourceWarning -m unittest discover -s osat_edge -t . -p "test_*.py" -v`
  before handoff.

## Architecture PDF and cumulative changelog

- 0.2.6 application code, tests, resources and runtime requirements are frozen.
  Future application changes require a new version.
- Every code modification must update only affected sections in
  `docs/ARCHITECTURE_GUIDE.md`, append its version entry in `docs/CHANGELOG.md`,
  and regenerate the current PDF. Preserve unaffected prose and prior history.
- Follow `docs/PDF_RELEASE_WORKFLOW.md`; keep stable section IDs, plain English,
  high contrast, readable diagrams/tables and current evidence limitations.
- Visually inspect the PDF and include exactly one `OSAT_SemiGuard_Architecture.pdf`
  directly inside the release ZIP's project root, together with its editable sources.
- Use the documentation renderer's `--package` step; the unchanged 0.2.6 builder
  alone does not add the root PDF. No release may omit or ship a stale guide.
