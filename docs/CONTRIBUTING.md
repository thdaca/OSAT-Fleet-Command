# Make a small, safe contribution

Choose [your team](teams/README.md), read the owning stage README, then inspect
its input/output contracts and one behavior test. Keep a change focused on one
question: validation, a feature, a model comparison, a screen detail or a claim.

Tests live beside their stages. Step03 covers Steps01–03; Step07 covers
Steps04–07; Step15 covers Steps10–15. PRE01's `tests/support.py` contains shared
test fixtures and is never runtime code.

## Verify

From the repository root with the README's Python environment:

```powershell
.venv\Scripts\python -m unittest osat_edge.roadmap.steps.step08_live_telemetry.tests.test_step08_telemetry -v
.venv\Scripts\python -W error::ResourceWarning -m unittest discover -s osat_edge -t . -p "test_*.py" -v
```

Replace the first module with your stage's test. UI tests in
`osat_edge.ui.tests.test_ui` run offscreen. Existing tests and snapshot 1 parity
checks protect numerical behavior, rejected inputs, UNKNOWN and authority.
Keep meaningful assertions when moving code. Layout assertions may follow the
new layout; safety and numerical assertions must still hold. Add tests for new
behavior or regressions, not tests that simply restate trivial implementation.

## Collaborate and keep boundaries

Handoffs identify machine/family, origin, source identity, units and semantics,
training/validation separation, supported conclusion, limitations and the next
experiment. Ask the owning team to review source mappings, healthy intervals,
physics assumptions, scoring, thresholds, evidence interpretation or authority.
Negative results and abstentions belong in the handoff.

- Use ordinary Python and small dataclasses. A helper should clarify an actual
  responsibility; avoid dynamic frameworks and forwarding layers.
- Put code, tests and resources in their numbered stage; put presentation in
  its screen. Import functions from their owner, without old-path shims.
- Explain assumptions and rejection reasons. Keep ordering and calculations
  deterministic and missing evidence explicit.
- Never grant authority through UI, retrieval, LLM prose or external research.
- Put outputs in `.artifacts/` and raw datasets in `benchmarks/_external/`.

## Release identities

A draft code edit may pass its targeted tests while the PoC reports source
identity drift. The release pins intentionally detect changed implementation
bytes. Do not adjust expected hashes just to silence tests. A release maintainer
reviews behavior and science reproduction, then updates current pins and the
PoC report together. Historical evidence stays intact. See [release guidance](RELEASES.md).
