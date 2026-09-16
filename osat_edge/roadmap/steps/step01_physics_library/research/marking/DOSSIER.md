# Laser marking physics dossier

## Mechanism

A marker converts a command into delivered optical output through an
architecture-specific source, controller, pulse regime, and optical path.
Direct measured output at a defined plane is more defensible than assuming a
diode-current/temperature relationship for an unknown laser architecture.

## Candidate measurable relation

`marking.commanded_measured_laser_output_stability`: compare commanded output
with measured optical output within a frozen architecture/control/pulse/
temperature regime and validate the internal monitor against an external
reference.

## Exact variables and units

Commanded and measured optical output `W` (or pulse energy `J` when the OEM
defines that command); pulse rate `Hz`; pulse duration `s`; duty ratio
dimensionless; temperature `°C`; control mode and optical-plane identity `state`.

## Available OEM/process signals

KEYENCE documents built-in thermopile output monitoring during marking and its
maintenance use. MK-01 names delivered power, drive current, and temperature,
but lacks the command, optical plane, architecture, and monitor semantics.

## Confounders

Laser architecture, control mode, pulse/duty/Q-switch state, temperature,
optical-path contamination and attenuation, focus/working distance, internal
monitor drift, downstream optics, material, and command saturation.

## Parameter identifiability

Command-to-output behavior is identifiable only for one architecture and
control/pulse regime with a calibrated reference plane. Electrical current
cannot be interpreted without source and controller architecture.

## Calibration domain

One exact marker, fixed source/controller configuration and optical plane,
bounded command/pulse/temperature ranges, and separate attenuation/reference
tests.

## Uncertainty sources

Internal and external power calibration, spectral response, sampling plane,
pulse aggregation, temperature lag, alignment/focus, contamination, and drift.

## Falsification criteria

Reject if command/output behavior is not repeatable, internal and external
measurements disagree without explanation, or monitor/path/focus controls mimic
source degradation.

## Minimum machine experiment

Sweep approved output commands and thermal/pulse states; compare the built-in
monitor with a calibrated external meter; introduce safe downstream attenuation;
challenge internal-monitor gain, controller mode, focus, and optical path.

## Source quality

KEYENCE is direct commercial marker documentation for measured optical output
and maintenance; TRUMPF is broader vendor condition-monitoring evidence. Both
are vendor-specific, not MK-01 validation.

## Measurement-semantics maturity

`LITERATURE_SUPPORTED`; command/output/plane/control definitions are unverified.

## Status

`RESEARCH_ONLY`. Laser electrical-current relationships stay non-executable
until the actual source architecture and telemetry are established.
