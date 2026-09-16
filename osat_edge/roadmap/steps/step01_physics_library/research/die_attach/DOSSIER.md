# Die attach physics dossier

## Mechanism

Two boundaries are recorded. Leak-rate inference needs a controlled isolated
volume; running nozzle vacuum cannot identify leakage. A modern closed-loop
bond head controls placement force along a Z trajectory while thermal and tool
state can affect the response.

## Candidate measurable relation

- `die_attach.nozzle_vacuum_leak_rate`: rejected for current telemetry.
- `die_attach.closed_loop_force_z_temperature_consistency`: research-only
  comparison of force command/feedback conditioned on actual Z, cycle phase,
  internal/bond-head temperature, tool, and material context.

## Exact variables and units

Force command/feedback `N`; actual Z `µm`; internal/bond-head temperature `°C`;
cycle phase/control mode `state`. For an offline leak test only: pressure `kPa`,
isolated volume `m^3`, time `s`, temperature `°C`, and leak rate `Pa*m^3/s`.

## Available OEM/process signals

DA-01 presently names nozzle vacuum, Z-axis current, Z-position error, stage
temperature, and settle time. Besi 9800 TC next documentation specifies bond
force, bond-head Z control/accuracy, bond-head thermal control, bond traces, and
inline process monitoring; it does not prove DA-01 exposes equivalent signals.

## Confounders

Control mode and gains; command profile; tool/compliance; adhesive and material;
surface/topography; thermal gradients; phase/window; sensor path; velocity and
settling. For vacuum: pump/valve state, outgassing, virtual leaks, and volume.

## Parameter identifiability

Force/Z/temperature consistency is identifiable only within one machine,
control mode, tool/material regime, and synchronized phase. Z-axis current is
not force without drive/mechanism semantics.

## Calibration domain

One exact die bonder with calibrated force/Z/temperature measurements, fixed
controller/tool configuration, and explicit phase/window boundaries.

## Uncertainty sources

Force and Z calibration, temperature location/lag, phase alignment, tool
compliance, material variation, control saturation, and reference drift.

## Falsification criteria

Reject if held-out profiles are not repeatable, temperature/tool/context effects
cannot be bounded, or force/Z/temperature sensor faults mimic the target.

## Minimum machine experiment

Run approved force/Z/temperature sweeps with command and feedback traces; block
by tool/material; include force, Z, temperature, phase, and control-mode negative
controls. A leak experiment requires a separate known-volume isolation setup.

## Source quality

Besi is direct modern OEM capability evidence but model-specific. Leybold is a
technical source for pressure-rise leak testing, not die-bonder validation.

## Measurement-semantics maturity

Both records are `LITERATURE_SUPPORTED`; DA-01 semantics are unverified.

## Status

Vacuum leak rate is `REJECTED`. Closed-loop force/Z/temperature consistency is
`RESEARCH_ONLY`. Neither has runtime output.
