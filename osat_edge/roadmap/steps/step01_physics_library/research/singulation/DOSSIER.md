# Singulation physics dossier

## Mechanism

Package singulation can use a high-speed dicing spindle whose electromechanical
load influences reported current under bounded drive/control assumptions. The
process context differs from wafer saw and must be studied independently.

## Candidate measurable relation

`singulation.spindle_current_speed_residual`: an SG-specific
**electromechanical spindle-load consistency** research relation:

`r_I_SG = I_SG - (a_SG_machine n_SG + b_SG_machine)`

It is not executable. SG coefficients, envelope, and evidence must never be
copied from WS-01.

## Exact variables and units

Actual SG spindle speed `RPM`; verified drive current `A`; residual `A`;
SG-only fitted slope `A/RPM` and intercept `A`; feed `mm/s`; cut depth `mm` or
`µm`; coolant flow `L/min`; temperature `°C`; blade/tool, package/material,
cutting phase, and control mode `state`.

## Available OEM/process signals

DISCO explicitly lists DAD3660 package-singulation use and spindle-current
condition monitoring. SG-01 names spindle speed/current and blade vibration,
but its equipment identity and signal semantics are not established as DAD3660.

## Confounders

Feed/cutting state; blade/tool type, dressing and wear; package/material stack;
coolant/water drag; cut depth; acceleration; drive/controller; temperature;
fixture; dual-spindle operating state; current and speed filtering.

## Parameter identifiability

Only SG-specific exact-machine calibration can identify the nuisance slope and
intercept. Current/speed alone cannot localize wear or separate process load,
coolant drag, controller changes, and sensor drift.

## Calibration domain

SG-01 only, after machine and drive semantics are verified; fixed tool/package/
coolant/control regime; robust multi-speed excitation; no extrapolation; later
held-out blocks. No WS calibration or baseline is permitted.

## Uncertainty sources

Current/speed calibration and filtering, alignment, process context, coolant,
tool/package variation, controller state, vibration path, and label boundaries.

## Falsification criteria

Reject if the SG-only residual is not repeatable, retains unbounded context
dependence, fails controlled load tests, or sensor/context faults mimic change.

## Minimum machine experiment

Repeat the spindle study on the actual singulation machine with traceable speed/
current references, feed/tool/package/coolant/phase context, SG-only calibration,
held-out validation, and sensor-fault challenges.

## Source quality

The DISCO DAD3660 page is direct OEM evidence for package singulation and
spindle-current monitoring. It does not prove SG-01 model identity, current
semantics, fault sensitivity, or parameter transferability.

## Measurement-semantics maturity

`LITERATURE_SUPPORTED`; SG-01 signal and equipment semantics are unverified.

## Status

`RESEARCH_ONLY`. WS and SG remain separately calibrated, and only the WS
relation is on the runtime research path.
