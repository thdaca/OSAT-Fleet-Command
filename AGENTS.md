# Repository rules

OSAT Fleet Command 0.2.4 is a research/development student project, not production software.

- Keep PRE01–PRE03 in `osat_edge/roadmap/pre_steps/`, Step01–Step15 in
  `osat_edge/roadmap/steps/`, and POST01–POST04 in
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
- Do not call a risk score a failure probability.
- Do not add compatibility layers for deleted pre-0.2.0 architecture.
- Run `python -W error::ResourceWarning -m unittest discover -s osat_edge -t . -p "test_*.py" -v`
  before handoff.
