# Your first hour in SemiGuard

SemiGuard asks whether trustworthy measurements support a change in machine
condition and shows the evidence. The project is named OSAT SemiGuard;
the demonstrations are synthetic.

1. Follow [setup](README.md), run `demo`, then open `ui`.
2. Select WS-01, inspect its telemetry/model/subsystem evidence, inject the demo
   spindle fault and read the ticket. Disconnect input and notice LAST KNOWN.
3. Choose [your team](docs/teams/README.md); read its entry file and one test.
4. Follow [one sample through the system](docs/ARCHITECTURE.md).
5. Make a narrow change using [the contribution guide](docs/CONTRIBUTING.md).

## Understand the folders before the algorithms

PRE-STEPS establish identity, channel meaning, origin and source trust. STEPS
implement physics, features, models, deterministic health and maintenance.
POST-STEPS demonstrate and test those stages and run isolated external research.
The architecture remains **PRE-STEPS → STEPS → POST-STEPS**.

Features summarize measurements; residuals compare measurements with physical
relations; models compare features with healthy references. Health uses eligible
evidence and persistence. Fault evidence and eligible demo tickets follow health.
The UI displays these decisions. Each screen has its own class in `ui/screens/`.

Each numbered stage owns its implementation, tests, research and resources.
Its README gives inputs, outputs, owners, entry files and a targeted test command.
Use [the roadmap](osat_edge/roadmap/README.md) and [glossary](docs/GLOSSARY.md).

## Teams and handoffs

Failure Research investigates failure modes per machine, their physics,
subsystems, sensors and parameters, then explains whether each could be modeled.
Data Pipeline owns correct parsing, end-to-end integration, consistency and
functional validation of the whole system. ML builds the core computer-run
algorithm, including machine learning, to address those physical problems through
that pipeline. Reliability examines full-pipeline results for statistical sense,
overfitting, leakage and other weaknesses. UI makes the whole system clear to
maintenance engineers and factory floor managers, guided by plant requirements.

Reliability may return SUPPORTED, REVISE, COLLECT MORE DATA or ABSTAIN with limits.
The loop goes back when evidence fails; a negative result is useful. Data Pipeline's
whole-system functional checks and Reliability's statistical checks complement
each other. The 0.2.6 application is frozen; documentation and research explanations
can improve, while future application changes require a new version.

## Rules on your first contribution

- Exact-machine history and models cannot cross machine identity or family.
- Mode describes execution; origin describes evidence. REAL_REPLAY is not REAL_OSAT.
- UNKNOWN means insufficient supported evidence, neither healthy nor a failure.
  Do not substitute NORMAL, zero or cached healthy state for missing evidence.
- An anomaly is not causal proof; a risk score is not a failure probability.
- Live equipment and REAL_OSAT replay are observe-only. SHADOW forbids control.
- Retrieval and the local LLM only add validated wording after deterministic
  demo-ticket evidence. They cannot decide health or grant authority.
- Outputs belong in `.artifacts/`; raw datasets stay in `benchmarks/_external/`.
  Read [release guidance](docs/RELEASES.md) before changing pinned records.

Start with a feature explanation, a telemetry rejection test, a screen label,
an evidence interpretation or a physics dossier. Your team guide gives bounded
examples. You do not need to understand every stage before making one contribution.
