# Words used in the code

- **OSAT:** outsourced semiconductor assembly and test.
- **Family:** an equipment type; **exact machine:** one installed identity.
- **Canonical channel:** an approved measurand with units, subsystem, source ID
  and timing requirements. **Telemetry:** its measurements.
- **Asynchronous:** each channel has its own timestamps/sample period; no
  synchronized row of every sensor is assumed.
- **Feature window:** the bounded interval summarized by a feature.
- **Median / MAD:** robust central value / median absolute deviation.
- **Residual:** measured behavior minus a physical relationship's expected
  behavior; evidence rather than proof of a cause.
- **Calibration:** estimating parameters and checking their applicable domain.
- **Context:** equipment state such as PROCESSING or IDLE; healthy behavior can differ.
- **Baseline:** confirmed-healthy model for one machine/context.
- **Deviation:** a difference from the healthy reference.
- **Hysteresis:** different entry/exit thresholds; **persistence:** evidence
  lasts a specified time before transition.
- **Risk score:** uncalibrated advisory score, not a failure probability.
- **Confounder:** another condition that could explain the apparent effect.
- **Leakage:** evaluation-target information unintentionally affects training.
- **Held-out evidence:** data reserved from training for honest evaluation.
- **Provenance:** identity, origin and permitted interpretation of evidence.
- **SHA-256 / digest:** byte identity detecting changes, not a signature,
  authorization, valid measurement guarantee or proof of model quality.
- **RAG / LLM:** retrieved local guidance / optional local model for ticket prose.
- **SECS/GEM / HSMS:** equipment communication concepts exercised by a bounded
  report adapter and optional loopback simulator here.
- **SHADOW:** observing and presenting without equipment control.
- **UNKNOWN:** evidence cannot support a health classification.
