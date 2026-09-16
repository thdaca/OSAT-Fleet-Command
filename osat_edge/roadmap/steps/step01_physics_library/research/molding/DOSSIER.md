# Molding physics dossier

## Mechanism

Semiconductor transfer molding coordinates clamp force, transfer pressure,
temperature zones, cavity vacuum, press/plunger phase, tool geometry, and resin
state. Equipment consistency can be studied only as a phase-resolved,
context-conditioned multivariable relationship.

## Candidate measurable relation

`molding.clamp_transfer_temperature_consistency`: compare actual clamp-force and
transfer-pressure profiles conditional on multi-zone mold temperatures, phase,
vacuum, tool, and material/cure context. It is not an executable force balance.

## Exact variables and units

Clamp force `N`; transfer/cavity pressure `MPa`; temperature zones `°C`; cavity
vacuum `kPa` with absolute/gauge convention; plunger/press position `mm`; time
`s`; phase, tool, material, and control mode `state`.

## Available OEM/process signals

Besi/Fico documents dynamic clamping control, active clamp-force level control,
dynamic transfer-pressure control, accurate multi-zone temperature control, and
board/cavity/foil vacuum. MO-01 names cavity pressure, clamp pressure, transfer
motor current, mold temperature, and position error, but not their full semantics.

## Confounders

Tool/cavity geometry, projected area, resin batch/rheology/cure, material,
temperature distribution, vacuum, cycle phase, transfer speed, hydraulic/servo
losses, sensor locations, maintenance state, and controller configuration.

## Parameter identifiability

A profile baseline is identifiable only for one machine/tool/material/control
regime with direct clamp-force and transfer-pressure feedback. Hydraulic
pressure or motor current alone does not identify actual clamp force.

## Calibration domain

One exact mold press, fixed tool/cavity and material class, documented force/
pressure/temperature/vacuum paths, synchronized phase, blocked lots, and held-out
chronological repeats.

## Uncertainty sources

Force/pressure calibration, zone-temperature accuracy and gradients, phase
alignment, cavity distribution, resin variability, vacuum definition, and drift.

## Falsification criteria

Reject if profiles are not repeatable within regime, material/tool/temperature
effects cannot be bounded, or sensor/phase controls mimic equipment change.

## Minimum machine experiment

Run approved blocked force/pressure/temperature/vacuum sweeps with direct
feedback and phase/position; include sensor bias, material, tool, zone, vacuum,
and phase negative controls; freeze calibration before held-out evaluation.

## Source quality

Besi/Fico is direct OEM capability evidence. Kahle and Kaya provide electronic-
packaging transfer-mold process-monitoring evidence. None validates MO-01.

## Measurement-semantics maturity

`LITERATURE_SUPPORTED`; actual MO-01 force, transfer-pressure, temperature-zone,
vacuum, and phase semantics are missing.

## Status

`RESEARCH_ONLY`. No runtime relation or threshold is added.
