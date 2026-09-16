# Wafer saw physics dossier

## Mechanism

With stable drive/control semantics, spindle electromechanical load can affect
reported current. Speed explains only part of healthy current. Feed/cutting
state, blade/tool state, material, coolant/water drag, temperature, acceleration,
and controller behavior remain important nuisance mechanisms.

## Candidate measurable relation

The existing executable research relation is the **electromechanical
spindle-load consistency residual**:

`r_I = I_reported - (a_machine n_actual + b_machine)`

It is evaluated only inside the exact-machine calibrated speed envelope. Its
equation and numerical implementation are unchanged. It is not cutting force.
The coolant pressure/flow candidate remains separate and research-only.

## Exact variables and units

- Actual spindle speed `n_actual`: `RPM`.
- Reported drive current `I_reported`: `A`, with phase/RMS/DC-bus and filtering
  semantics documented.
- Residual `r_I`: `A`; slope `a_machine`: `A/RPM`; intercept `b_machine`: `A`.
- Feed `mm/s`, cut depth `µm` or `mm`, coolant flow `L/min`, pressure `kPa`,
  temperature `°C`, and categorical cutting/blade/material states as context.

## Available OEM/process signals

DISCO lists spindle-current monitoring as a DAD3660 condition-monitor function.
The repository has `spindle_speed` and `spindle_current`, but controller and
acquisition semantics remain unverified.

## Confounders

Coolant/water drag; feed/cutting state; cut depth; blade/tool identity, dressing,
wear, and clogging; work material; temperature; acceleration; drive efficiency,
control mode, filtering, and firmware.

## Parameter identifiability

Slope/intercept are exact-machine nuisance parameters, not universal physics.
They require multiple speed levels and cannot separate process load, drive loss,
coolant drag, or fault cause without added context/reference measurements.

## Calibration domain

WS-01 only; same spindle/drive/sensor configuration and documented process
regime; at least 20 healthy samples, six speed levels, robust span, and no
extrapolation. Parameters must never be shared with SG-01.

## Uncertainty sources

Current and speed scaling/filtering, timestamp/drive lag, sensor offset/drift,
omitted process state, nonlinear/regime behavior, and fault-label uncertainty.

## Falsification criteria

Reject if the held-out residual retains material speed/feed/tool/material/
coolant dependence, if controlled load produces no repeatable response, if
sensor faults are indistinguishable, or if chronological coefficients drift.

## Minimum machine experiment

Use traceable current and tachometer references, record feed/cut/tool/material/
coolant/phase context, randomize safe load conditions, freeze early healthy
calibration, and validate on later blocks with sensor-fault controls.

## Source quality

DISCO DAD3660 is direct OEM capability evidence. US6168500B1 is patent evidence.
UTAC supplies real-OSAT industrial-practice evidence but no public telemetry.
TUHH DAD3350 data are real target-process measurements, not health validation.

## Measurement-semantics maturity

`LITERATURE_SUPPORTED`; WS-01 current/speed semantics and physical validation
remain incomplete.

## Status

`RUNTIME_RESEARCH` for the unchanged WS relation; observe-only research evidence.
The coolant candidate is `RESEARCH_ONLY`. Neither is a probability or causal
diagnosis.
