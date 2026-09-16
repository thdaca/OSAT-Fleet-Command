# Wire bond physics dossier

## Mechanism

The ultrasonic generator/transducer/tool/contact system presents a dynamic
electrical and mechanical load during specific bond phases. Machine-reported
current and impedance can be interpreted only under their controller/OEM
definitions and a precisely aligned bond window.

## Candidate measurable relation

- Legacy `wire_bond.ultrasonic_input_impedance`: remains rejected because the
  low-rate repository channels cannot reconstruct phase-resolved impedance.
- `wire_bond.ultrasonic_generator_electrical_load_consistency`: research-only
  phase-specific comparison of explicitly defined machine-reported electrical
  load. It does not derive `Z=V/I` from PTI fields.

## Exact variables and units

USG current `mA` (or source-declared unit); voltage where available `V`; drive
frequency `Hz`; phase `rad` or `deg`; machine-computed impedance in its exact
OEM-declared unit/definition; bond force `gf` or source-declared unit; Z values
`µm` or source-declared unit; phase/window and control mode `state`.

## Available OEM/process signals

The PTI OSAT study reports exactly: Capillary Count, Bond Height Delta,
Deformation, Die Height, Die Tilt, Bond Force, USG Impedance, USG Current,
Z at Contact, and Z at End of Bonding. WB-04 presently names bond force,
ultrasonic current, frequency shift, bond-head current, and clamp temperature.
Names do not prove equivalence.

## Confounders

Generator control mode; current/voltage path; drive frequency; impedance
definition; bond phase/window; ultrasonic power/time; bond force; tool/capillary
identity and wear; wire/pad/material; temperature; machine and recipe context.

## Parameter identifiability

No electrical-load baseline is identifiable until units, path, control mode,
frequency, phase/window, tool, and exact machine are fixed. Machine-computed
USG Impedance must not be assumed to equal a derived electrical impedance.

## Calibration domain

WB-04 only, one generator/transducer configuration, fixed control mode,
tool/capillary and pseudonymous context, defined bond phase/window, and
independent later validation.

## Uncertainty sources

Current/voltage gain and phase, machine-impedance algorithm, trigger alignment,
frequency aggregation, tool identity, inspection labels, and controller changes.

## Falsification criteria

Reject if phase-aligned values are not repeatable, tool/context effects dominate,
inspection outcomes do not relate to the target equipment question, or gain/
phase/window faults reproduce the candidate response.

## Minimum machine experiment

Obtain the narrow de-identified fields in `WB04_DATA_REQUEST.md`; establish the
field dictionary; run approved tool/contact conditions with independent
inspection/maintenance outcomes and electrical/window negative controls.

## Source quality

DOI 10.32604/cmc.2026.078762 is peer-reviewed real-OSAT evidence and explicitly
makes confidential data requestable from the corresponding author. It is not a
public raw dataset. Feng et al. supports dedicated voltage/current/phase methods
but does not validate PTI field semantics.

## Measurement-semantics maturity

`LITERATURE_SUPPORTED`; no engineering units, raw records, or WB-04 signal-path
definitions have been verified.

## Status

Legacy impedance is `REJECTED`; the narrower electrical-load consistency
hypothesis is `RESEARCH_ONLY`. No paper-only evidence creates an OSAT score.
