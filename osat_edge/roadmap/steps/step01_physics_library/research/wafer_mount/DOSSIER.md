# Wafer mount physics dossier

## Mechanism

Dicing tape is stretched and laminated onto a frame. Mounted tension can vary
with tape properties, frame deformation, stretching, rollers, lamination
settings, environment, and time. The defensible measurand is direct per-frame
tension (or a validated optical indicator), not inferred roller motor current.

## Candidate measurable relation

`wafer_mount.dicing_tape_tension_stability`: compare a direct tension indicator
with a frozen baseline for the same tape/roll/frame/lamination regime. This is a
drift/stability hypothesis, not a universal threshold or runtime equation.

## Exact variables and units

- Direct tension indicator: `N`, with axis, frame state, and measurement method.
- Optional roller current: `A`, only with documented current/torque semantics.
- Roller speed: `rad/s`; temperature: `°C`; elapsed time: `s`.
- Tape manufacturer/type/material, roll, frame, and lamination setting:
  pseudonymous categorical context (`state`).

## Available OEM/process signals

Repository names include `web_tension`, `roller_motor_current`, and
`roller_temperature`. Their names do not establish measurement path or
calibration. The Infineon patent describes automated optical inspection and
per-tape tension data linked to a wafer identifier.

## Confounders

Tape manufacturer/type/material properties; roll identity and roll changes;
lamination roller settings; applied stretch; frame deformation; measurement
axis/location; temperature; time after lamination; friction and acceleration.

## Parameter identifiability

A baseline is identifiable only inside a fixed, recorded regime with repeated
direct measurements. Roller current cannot identify tension unless actual
machine torque/current semantics, geometry, acceleration, and losses are known.

## Calibration domain

One exact wafer mounter, one reviewed measurement method, fixed tape/roll/frame
class and lamination configuration, with blocked material and roll changes.

## Uncertainty sources

Tension-reference calibration, optical conversion, frame placement, anisotropy,
temperature/time drift, sensor drift, and regime misclassification.

## Falsification criteria

Reject if held-out direct tension is not repeatable within regime, if material
or roll effects dominate unrecorded variation, or if sensor/placement controls
mimic the claimed drift.

## Minimum machine experiment

Randomize safe tension and lamination changes on approved frames; block by tape
maker/type/material and roll; retain chronological repeats; include sensor
offset, material-change, roll-change, and optional current-at-fixed-tension
negative controls.

## Source quality

Infineon EP3705862B1 / US20200286795A1 is a directly relevant patent disclosure.
It identifies process variables but is not independent validation. Branca et
al. supplies general web-dynamics support only.

## Measurement-semantics maturity

`LITERATURE_SUPPORTED`; direct tension method, calibration, context, and
optional drive semantics remain unverified for WM-01.

## Status

`RESEARCH_ONLY`. No executable relation, threshold, health score, or claim that
motor current represents tension.
