# Repository rules

OSAT Fleet Command 0.2.2 is a research/development student project, not production software.

- Keep the numbered modules in `osat_edge/roadmap/` aligned with the documented roadmap.
- Prefer explicit ordinary Python and small dataclasses over framework-like indirection.
- Preserve machine-family and exact-machine identity checks.
- Preserve asynchronous per-channel telemetry and fail-closed source-ID mapping.
- Keep synthetic evidence separate from real OSAT evidence.
- LIVE_EQUIPMENT is observe-only. Only SIMULATION may create maintenance tickets.
- Health is deterministic. RAG and the optional local LLM may enrich a ticket, never create it.
- Do not call a risk score a failure probability.
- Do not add compatibility layers for deleted pre-0.2.0 architecture.
- Run `python -W error::ResourceWarning -m unittest discover -s tests -v` before handoff.
