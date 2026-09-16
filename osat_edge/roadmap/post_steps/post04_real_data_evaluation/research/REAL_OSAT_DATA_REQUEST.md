# Minimum de-identified REAL_OSAT data request

This is the reusable minimum request for evaluating OSAT Fleet Command 0.2.4
against retrospective wire-bond or comparable equipment-health data. The goal
is to obtain enough provenance and measurement meaning for an honest frozen-
method evaluation without collecting customer process IP.

## Required source identity and boundaries

- A pseudonymous exact-machine ID that remains stable across all files.
- Equipment family and canonical station; OEM/model only when releasable.
- A statement identifying the source as an OSAT facility/operator.
- Source citation, dataset/version, transfer date, license/access terms, and a
  SHA-256 for every authoritative source file.
- Timezone-aware timestamps or documented relative time, plus unambiguous
  machine, run, lot, and cycle/bond boundaries where they exist.
- Sampling/acquisition semantics for every field: event-driven or periodic,
  sample interval/rate, aggregation window, point-in-cycle meaning, missing-
  value convention, and whether a value is measured feedback, controller
  estimate, setpoint, or derived statistic.

## Required channel dictionary

For every proposed equipment-health signal, provide its exact source name,
engineering unit, physical meaning, sensor/controller origin, calibration or
scale convention when releasable, and machine subsystem. For a PTI-like
wire-bond export, the fields to review are:

- Capillary Count;
- Bond Height Delta;
- Deformation;
- Die Height;
- Die Tilt;
- Bond Force;
- USG Impedance;
- USG Current;
- Z at Contact;
- Z at End of Bonding.

No field will map to `WB-04` merely because its name is similar. For example,
`Bond Force` needs force units and feedback semantics before it can map to
`bond_force` (`gf`), and `USG Current` needs current units and sampling meaning
before it can map to `ultrasonic_current` (`mA`). USG impedance remains
statistical/exact-machine evidence unless synchronized voltage, current, phase,
and bond timing support a separately reviewed physical relation.

## Required context and labels

- Opaque recipe/context IDs that preserve grouping and chronology without
  disclosing recipe values.
- Machine alarm events with code category, start/end time, and machine ID.
- MES scrap or inspection outcomes with time/run linkage and an explicit label
  type.
- Maintenance events, work-order timestamps, and component/subsystem involved,
  where available.
- Independently adjudicated healthy intervals and fault intervals, including
  adjudicator role and basis, where available.

Keep label types separate. Scrap and process-quality outcomes are not machine
failures; alarms are not confirmed faults; maintenance work is not necessarily
a fault; and the absence of alarms or maintenance does not establish confirmed
healthy history.

## Acceptable anonymization

Customer, product, device, lot, and recipe identities may be consistently
pseudonymized. Exact recipe values, PPIDs, wafer maps, geometry, proprietary
process windows, and unrelated calibration/equipment constants are neither
requested nor accepted. An opaque context ID is sufficient when it preserves
run boundaries and allows chronology-safe comparison.

All partner bytes remain outside Git and release ZIPs. Retrospective evaluation
is research-only and cannot create an operational Step 15 maintenance ticket.

## UTAC / WS-01 minimum request

For the documented UTAC DISCO wafer-saw lead, a sufficient de-identified export
needs only:

- pseudonymous stable DISCO machine ID and model;
- timestamps plus run/wafer boundaries and machine state;
- spindle current and spindle speed with exact units and acquisition semantics;
- water/coolant channels with exact units, when available;
- alarm start/end events and categories;
- maintenance events, including blade change or dress events when available;
- independently adjudicated abnormal and healthy intervals when available.

Customer, product, recipe, PPID, wafer-map, geometry, and process-window values
are not requested. Opaque grouping IDs are sufficient. No field maps to WS-01
until its physical meaning and exact unit match the PRE02 registry.
