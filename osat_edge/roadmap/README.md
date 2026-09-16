# OSAT Fleet Command roadmap

```text
PRE01 common contracts
PRE02 canonical machine registry
PRE03 source and provenance validation
        |
        v
STEP01 physics library
STEP02 physical features
STEP03 physical residuals
STEP04 family data
STEP05 family model
STEP06 machine history
STEP07 exact-machine model
STEP08 telemetry
STEP09 health and risk
STEP10 fault evidence
STEP11a maintenance database
STEP11b OEM knowledge
STEP12 retrieval
STEP13 optional local LLM
STEP14 JSON validation
STEP15 deterministic maintenance ticket
        |
        v
POST01 deterministic demo
POST02 frozen reference replay
POST03 external benchmark
POST04 real-data and REAL_OSAT evaluation
```

`pipeline.py` remains the linear operational orchestrator. The sibling `ui/`
package contains human interfaces only. Research notes, tests, fixtures, and
resources owned by one stage live beside it in a matching `*_assets/` directory.
