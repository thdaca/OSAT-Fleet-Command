# Trim / form physics dossier

## Mechanism

Semiconductor trim/form systems use electric/servo cam presses to cut and form
packaged devices. Tool contact produces a stroke-dependent load shaped by drive
control, linkage, inertia, friction, package geometry, material, and tooling.

## Candidate measurable relation

`trim_form.stroke_aligned_servo_load_profile_consistency`: compare verified
servo load/torque feedback and reference punch-force profiles by actual stroke
position within one tool/package regime. Motor current is not punch force.

## Exact variables and units

Servo torque/load `N*m` or exact OEM load unit; reference punch force `kN`;
stroke position/angle `mm` or `rad`; velocity `mm/s`; acceleration `mm/s^2`;
motor current `A` only with drive semantics; tool and package geometry `state`.

## Available OEM/process signals

Gallant documents an electric cam servo trim/form line. Taijin documents a
semiconductor trim/form servo-motor punch capability of 3-5 ton. TF-01 names
punch force, press motor current, die vibration, and die temperature, without
the drive, stroke, package, or tooling semantics required here.

## Confounders

Package geometry and material; tooling identity, wear, clearance, and change;
stroke speed/acceleration; linkage/mechanical advantage; friction/lubrication;
temperature; servo gains/control mode; force/current sensor drift.

## Parameter identifiability

The profile is identifiable only with actual stroke position and verified servo
load/torque semantics. Mapping motor current to punch force additionally needs
motor/drive constants, transmission/linkage, inertia, losses, and force reference.

## Calibration domain

One exact trim/form machine, fixed drive and tooling configuration, one
pseudonymous package-geometry/material class, bounded stroke-speed range, and
phase-aligned high-rate acquisition.

## Uncertainty sources

Servo-load scaling, dynamic force calibration, phase alignment, encoder error,
mechanism compliance, friction, tool/package context, and temperature.

## Falsification criteria

Reject if held-out profiles are not repeatable, package/tool/kinematic effects
cannot be bounded, or current/force/encoder faults mimic the target response.

## Minimum machine experiment

Use calibrated dynamic force and stroke references; run safe randomized blocks
across tool condition, package geometry/material, stroke speed, and temperature;
include current/load, force, phase, acceleration, and friction controls.

## Source quality

Gallant and Taijin are directly relevant semiconductor-equipment OEM/product
sources. Their specifications establish architecture/capability, not TF-01
measurement semantics or a health relationship.

## Measurement-semantics maturity

`LITERATURE_SUPPORTED`; drive feedback, force, stroke, package, and tool context
remain unverified.

## Status

`RESEARCH_ONLY`. No current-to-force equation or runtime output is added.
