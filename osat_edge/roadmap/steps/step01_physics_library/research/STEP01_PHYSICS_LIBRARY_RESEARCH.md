# Step 01 Physics / Engineering Library — Maximum-Credibility Research Review

Version reviewed: OSAT Fleet Command 0.2.5  
Review date: 2026-09-03  
Release class: RESEARCH / DEVELOPMENT BUILD  
Physical validation complete: **NO**

Review type: structured engineering literature and model-credibility review;
this is not represented as a formal systematic review.

## Optional offline research tools

Step01's optional unit, symbolic, and experiment-design audits are isolated
from edge inference. Install them only when running Step01 research checks:

```text
python -m pip install -r osat_edge/roadmap/steps/step01_physics_library/resources/requirements-physics-research.txt
python osat_edge/roadmap/steps/step01_physics_library/resources/run_physics_research_audit.py
```

- Pint audits declared dimensions and repository unit spellings without
  rewriting canonical telemetry units.
- SymPy checks only explicitly coded symbolic identities; equation text is
  never dynamically evaluated.
- pydoe can translate explicitly supplied factor levels into deterministic
  design matrices. A generated design is not physical evidence and does not
  change any existing `ExperimentPlan` claim.

Dependency purposes, optional status, and license families are recorded in
`resources/DEPENDENCY_IP_INVENTORY.md`.

## A. Executive summary

Step 01 is an auditable registry of engineering claims, not an equation
collection and not a claim of plant validation. This pass deliberately leaves
only one relation on the runtime research path:

- `spindle.current_speed_residual`, for the `wafer_saw` family only.

That relation is **LITERATURE_SUPPORTED**, not bench validated. It produces an
exact-machine, speed-conditioned current residual only inside its calibrated
speed range. It must not be interpreted as force, failure probability, causal
diagnosis, or a universal spindle-health limit.

Two earlier runtime ideas were demoted:

- The singulation spindle relation is research-only because evidence from
  wafer dicing does not establish transferability to a different mechanism.
- Final-test contact resistance is research-only because channel names and
  units do not establish Kelvin sensing, contact isolation, settling, offset
  compensation, or exclusion of relay, lead, fixture, and DUT voltage.

Every machine family remains represented in the research catalog. Every record
states the required measurand, measurement method, evidence claim, missing
instrumentation, uncertainty and model-discrepancy sources, expected direction,
sensor failure modes, residual FMEA, falsification path, and a controlled
experiment. No present relation is claimed to have completed physical
validation.

## B. Physics is not an equation

Writing a dimensionally correct equation does not establish that repository
channels measure the variables in that equation. A defensible physical
residual requires all of the following:

- a mechanism tied to a named subsystem;
- a precisely defined measurand and sensor path;
- units, sign, timing, bandwidth, location, and operating-state semantics;
- identifiable parameters under adequate excitation;
- an applicability envelope and an explicit refusal to extrapolate;
- controlled sensitivity to a target fault or degradation mechanism;
- bounded response to nuisance variables and negative controls;
- separation of measurement uncertainty from model-form discrepancy;
- a plan to detect sensor faults that can mimic degradation;
- held-out physical evidence appropriate to the intended use.

Ohm's law, motor torque constants, pressure-rise relations, and force balances
can all be correct while a proposed telemetry residual is invalid. For example,
`V/I` has resistance units, but it is not contact resistance unless `V` is the
contact-local voltage and `I` is the corresponding current under a valid
measurement procedure.

## C. Review methodology

The review used a claim-by-claim process:

1. Inspect the current machine profiles and canonical channels.
2. State the smallest proposed mechanism without adding unobserved variables.
3. Identify the exact measurands needed for the mechanism.
4. Search standards, metrology guidance, peer-reviewed work, OEM technical
   material, patents, and application notes for evidence and scope limits.
5. Record what each source supports and what it does not support.
6. Test dimensional meaning, sign, timing, bandwidth, location, and path.
7. Identify structural and practical identifiability limitations.
8. Separate measurement uncertainty, parameter uncertainty, operating
   variability, alignment error, and model discrepancy.
9. Enumerate target sensitivities, cross-sensitivities, sensor faults, and
   falsification tests.
10. Assign the conservative evidence maturity and lifecycle status.
11. Permit Step 03 execution only for `RUNTIME_RESEARCH` records.

This review verifies software behavior using synthetic arrays. That is software
verification only. It does not increase physical-evidence maturity.

## D. Search strategy and review date

The original structured review searches were performed through 2026-08-31; a
narrow named-source evidence update was completed on 2026-09-04. Preference was given to official
standards pages, BIPM/JCGM and NIST publications, DOI landing pages or publisher
records, OEM documentation, and the original patent record. Search concepts
included:

- physics-informed PHM and system health management;
- diagnostic residual robustness and model discrepancy;
- structural and practical parameter identifiability;
- measurement uncertainty, traceability, and calibration;
- dicing spindle current, speed, load, force, and vibration;
- dicing-saw spindle power and operating-speed scope;
- Kelvin/four-wire contact-resistance measurement and wafer-probe contact;
- web-tension roller dynamics;
- vacuum pressure-rise leak testing;
- wire-bond generator voltage/current impedance;
- transfer-molding cavity pressure and force;
- laser-marker optical power and condition monitoring;
- motor torque/current and mechanism-to-force mapping.

Sources that could not be verified sufficiently were not used as support.
Preprints, patents, vendor application material, and vendor service pages are
labelled as such; they are not presented as independent validation.

## E. Source hierarchy and evidence boundaries

The library records a source type because different sources support different
claims.

1. Standards and metrology guides support terminology, measurement practice,
   condition-monitoring process, and applicability boundaries. They do not
   automatically validate an equipment relation.
2. Peer-reviewed primary research may support a mechanism within its actual
   apparatus, population, and operating conditions. Transfer must be proven.
3. Peer-reviewed reviews support research context and known limitations; they
   do not calibrate an OSAT machine.
4. OEM technical documents can establish product capabilities and operating
   scope, but not a universal physical relationship.
5. Manufacturer application notes can provide useful measurement practice,
   but must be checked against the actual instrument and topology.
6. Patents show that an implementation or idea was disclosed. They are not
   performance validation.
7. Preprints are provisional and must be identified as such.

SEMI E10, E58, and E116 provide relevant equipment state/performance context:
E10-0422 is current for RAM and utilization; E58-0703 is an older/inactive
automated RAM standard; E116 covers equipment performance tracking. None of
them makes the Step 01 residuals physically valid, and this project does not
claim compliance.

## F. Credibility framework

Each executable relation and research candidate carries:

- `EvidenceClaim`: the precise supported statement, references, scope, and
  limitation;
- `MeasurementRequirement`: measurand, unit, method, path, semantics, sign,
  timing, bandwidth, calibration, traceability, resolution, and present status;
- `ParameterSpec`: interpretation, unit, source, domain, excitation,
  identifiability, and recalibration triggers;
- separate measurement-uncertainty and model-discrepancy records;
- directional target-fault sensitivities and cross-sensitivities;
- sensor failure modes and residual FMEA;
- an experiment plan with negative controls, DOE, held-out validation,
  acceptance, rejection, recalibration, invalidation, and safety requirements.

The lifecycle states are `CANDIDATE`, `RESEARCH_ONLY`, `RUNTIME_RESEARCH`,
`INVALIDATED`, and `REJECTED`. Lifecycle status answers whether software may
execute a claim. Evidence maturity answers what physical evidence supports it.
The two concepts are intentionally separate.

The library audit rejects internally incomplete records, unknown reference
keys, fitted parameters without `ParameterSpec`, model-discrepancy entries
mislabelled as measurement uncertainty, and non-runtime records leaked through
`relations_for_family`.

## G. Metrology and measurement semantics

JCGM 200 defines the vocabulary needed to distinguish a channel label from a
measurand. JCGM 100 provides a framework for measurement models and uncertainty
propagation. ISO 10012 addresses measurement-management systems. ISO 17359 asks
condition-monitoring programs to define technique, accuracy, operating
conditions, acquisition rate, and measurement locations. ISO 16063-21 covers
comparison calibration of vibration transducers.

For every current repository channel used or considered by Step 01, the most
defensible status is generally:

`AVAILABLE_BUT_SEMANTICS_UNVERIFIED`

The repository supplies canonical names and units, but does not establish a
traceable sensor path, calibration certificate, bandwidth, controller filtering,
or contact/fixture topology. Missing contextual variables are marked `MISSING`.
No current channel is upgraded to
`AVAILABLE_AND_SEMANTICALLY_SUPPORTED` merely because tests can construct a
matching array.

High-value semantic checks include:

- actual versus commanded spindle speed;
- phase, RMS, DC-bus, or controller-estimated current;
- time interval and filtering represented by each sample;
- pressure reference and sensor location;
- flow branch and direction;
- force sensor location and dynamic response;
- optical measurement plane and spectral response;
- Kelvin force/sense topology and contact-path isolation.

## H. Identifiability

Raue et al. distinguish structural from practical identifiability. A familiar
equation may be structurally meaningful but its parameters remain practically
unidentifiable when excitation or measurement coverage is weak.

For the active spindle relation, constant speed cannot identify slope and
intercept. Calibration therefore requires at least 20 finite physical samples,
at least six distinct speed levels, and a robust speed span of at least 100 RPM
or 0.2% of median speed, whichever is greater. Those are software guards for a
research fit, not sufficient physical-validation criteria.

The other candidates have larger identifiability gaps:

- web tension needs motion phase, inertia, geometry, transmission, and friction;
- hydraulic resistance needs a defined pressure drop and geometry;
- vacuum leak rate needs a known isolated volume and valve/pump state;
- wire-bond impedance needs voltage, current, phase, and bond timing;
- clamp force balance needs actual force and approved projected area;
- laser output needs architecture, pulse, controller, and measurement-plane state;
- punch force needs stroke phase and mechanism parameters;
- contact resistance needs contact-isolated measurement topology.

## I. Applicability envelopes and extrapolation

The spindle fit records the 2.5th and 97.5th percentiles of healthy calibration
speed as inclusive applicability boundaries. Runtime computation discards
samples outside those boundaries. If fewer than three valid in-range samples
remain, it emits no physical feature.

This is refusal, not clipping and not extrapolation. The speed envelope is only
one dimension. Controller configuration, current semantics, blade/material,
feed, cut depth, coolant, temperature, and cycle phase also define the real
domain and remain research blockers until observed and validated.

No ISO 20816 vibration alarm is used. ISO 20816-3:2022 covers industrial
machinery above 15 kW and operating from 120 to 30,000 r/min. DISCO publicly
lists dicing-saw spindle examples around 1.8 kW and 60,000 min⁻¹. That mismatch
is an explicit example of why a published standard threshold cannot be copied
outside its stated machinery scope.

## J. Model discrepancy

Kennedy and O'Hagan treat model inadequacy as distinct from uncertain fitted
parameters. Brynjarsdóttir and O'Hagan show that ignoring discrepancy can bias
physical parameter inference and make uncertainty look too small.

For the spindle relation, model discrepancy includes omitted feed, depth,
material, blade state, coolant, acceleration, controller behavior, thermal
effects, and possible nonlinearity. These are not current-sensor uncertainty.
They can shift the residual even if both sensors are perfectly calibrated.

Every candidate records analogous omitted physics. The software does not invent
a discrepancy distribution or combine it into a false confidence interval.

## K. Uncertainty framework

The code separates five categories:

- measurement uncertainty;
- parameter uncertainty;
- time/alignment uncertainty;
- operating-condition variability;
- model discrepancy.

An optional helper implements scalar linear propagation:

`u_y² = J Σ Jᵀ`

It validates dimensions, finiteness, symmetry, and positive semidefiniteness.
It returns no uncertainty unless the caller supplies an actual Jacobian and
covariance. The project presently has no traceable plant-sensor uncertainty
budgets, so it does not fabricate distributions, coverage factors, or confidence
levels.

## L. Robust residual construction and diagnostics

The active relation fits a Huber regression after centering/scaling speed for
numerical conditioning. It returns parameters in physical units:

- current-speed slope in A/RPM;
- current intercept in A;
- healthy residual scale in A;
- calibrated speed span, lower bound, and upper bound in RPM.

Residual output is the median of aligned, finite, physically plausible,
in-envelope sample residuals. This protects against a minority of gross
outliers but does not make the relation fault-specific.

Offline diagnostics report:

- residual median and MAD;
- chronological first-half/second-half drift;
- dependence on a supplied conditioning variable;
- lag-one and maximum short-lag autocorrelation;
- finite output fraction;
- fraction outside the applicability envelope;
- deterministic chronological-block parameter stability.

Chronological blocks are used instead of bootstrap resampling because the main
question is stability over acquisition order, not a synthetic IID sampling
distribution.

## M. Fault sensitivity versus specificity

Sensitivity means a target perturbation moves a residual detectably. Specificity
means other causes do not create the same movement. The active spindle relation
has a literature-supported expectation that added load may increase reported
current at comparable speed. Blade wear/clogging sensitivity remains a
hypothesis.

A positive spindle residual can also result from feed/depth/material changes,
coolant behavior, acceleration, drive/control changes, temperature, current
offset, speed bias, or alignment error. The relation therefore cannot localize
cause and must not be described as causal blade diagnosis.

Each residual FMEA records `can_localize_cause=False` under present evidence.
Localization requires additional independent measurements or controlled
evidence—not more assertive labels.

## N. Sensor failure modes and negative controls

Sensor faults can mimic physical degradation:

- positive current offset can mimic extra spindle load;
- negative speed bias can produce an apparent positive current residual;
- stale or stuck speed/current can suppress or create residuals;
- pressure or flow bias can mimic hydraulic restriction;
- voltage offset or current-scale error can mimic high contact resistance;
- optical-power sensor drift can mimic laser degradation;
- force/current gain drift can mimic tooling changes.

Experiment plans therefore include negative controls such as injected sensor
offsets, independently measured references, no-cut/no-contact cycles, fixed-load
speed changes, fixed-resistance lead/relay changes, and thermal repeats. A
residual that cannot distinguish a target perturbation from a credible sensor
fault is not ready for authoritative use.

## O. Evidence maturity ladder

The exact ladder is:

1. `HYPOTHESIS` — plausible mechanism, not adequately supported for the item.
2. `LITERATURE_SUPPORTED` — relevant literature supports the bounded mechanism.
3. `MEASUREMENT_SEMANTICS_VERIFIED` — actual sensor path, measurand, timing,
   units, and state semantics have been verified.
4. `BENCH_VALIDATED` — controlled physical bench evidence passes a predeclared
   protocol with independent artifacts.
5. `SINGLE_MACHINE_VALIDATED` — held-out evidence on one identified machine.
6. `MULTI_MACHINE_VALIDATED` — evidence on at least two appropriate machines,
   including transfer/variation analysis.
7. `PROSPECTIVE_PILOT_VALIDATED` — preregistered prospective plant evaluation.

Software unit tests, synthetic simulation, successful demo execution, and a
clean internal audit do not count as bench validation. The code prevents an
executable relation from being declared `BENCH_VALIDATED` or higher without an
independently verified validation-evidence record. No present relation has such
a record.

The separate research-source access tiers are
`PUBLISHED_REAL_OSAT_STUDY`, `REQUESTABLE_REAL_OSAT_DATA`, and
`EXECUTED_REAL_OSAT_DATA`. They classify research evidence only and are not
operational `DataOrigin` values. See `EVIDENCE_CATALOG.md`; no Step01 source is
currently classified as executed real-OSAT data.

## P. Machine-family research review

The concise summaries below are backed by one owned dossier per family in the
matching subdirectory (`wafer_mount/` through `final_test/`). Those dossiers own
the detailed variables, confounders, identifiability, calibration, uncertainty,
falsification, experiment, source-quality, maturity, and status records.

### Wafer mount

Candidate: direct dicing-tape tension stability/drift within documented tape,
roll, frame, and lamination context. Infineon EP3705862B1 / US20200286795A1
supports per-tape tension monitoring and identifies material/roll/lamination
context. Roller motor current is not treated as tension without verified drive
semantics. Status: `RESEARCH_ONLY`, `LITERATURE_SUPPORTED`.

### Wafer saw

Active: exact-machine **electromechanical spindle-load consistency residual**.
DISCO explicitly exposes DAD3660 spindle current for condition monitoring, and
dicing research establishes coupled process dynamics. Feed/cutting state,
blade/tool, material, and coolant/water drag are explicit confounders. The
unchanged relation is not cutting force. Status: `RUNTIME_RESEARCH`,
`LITERATURE_SUPPORTED`.

Wang et al. (2026) additionally report 4H-SiC wafer-dicing experiments at five
explicit spindle speeds from 22,000 to 38,000 RPM with spindle-inverter current
in amperes acquired at approximately 20 Hz. The public article provides figures
and summarized measurements, not a downloadable machine-readable raw trace;
the work is not established as OSAT data. It therefore strengthens only the
current/speed research trail and does not change the equation, maturity,
calibration, threshold, or validation status.

Candidate: coolant hydraulic resistance. The current pressure name does not
define a differential pressure across a named restriction. Status:
`RESEARCH_ONLY`, `HYPOTHESIS`.

### Die attach

Candidate: nozzle vacuum pressure-rise leak rate. The equation needs known
isolated volume, valve and pump isolation, timed pressure data, and thermal
conditions. Running vacuum alone cannot identify leakage. Status: `REJECTED`,
`LITERATURE_SUPPORTED` as a test method but not as a runtime relation.

Candidate: closed-loop bond/placement-force consistency conditioned on Z,
phase, internal/bond-head temperature, control mode, and tool/material context.
Modern Besi documentation supports the measurement concept, not DA-01
semantics. Status: `RESEARCH_ONLY`, `LITERATURE_SUPPORTED`.

### Wire bond

Candidate: ultrasonic input impedance. Published work uses voltage plus current,
phase/harmonics, and bond-cycle timing or dedicated vibration. Present channels
cannot reconstruct that measurement. Status: `REJECTED`,
`LITERATURE_SUPPORTED`.

Candidate: ultrasonic-generator electrical-load consistency during a defined
bond phase. The PTI real-OSAT study supplies actual production field names but
not units or raw public records. Machine-computed USG Impedance is not assumed
to be derived impedance. Status: `RESEARCH_ONLY`, `LITERATURE_SUPPORTED`.

### Molding

Candidate: clamp-force / transfer-pressure / mold-temperature consistency.
Besi/Fico documents active/dynamic clamp-force and transfer-pressure control,
multi-zone temperature, and cavity vacuum. MO-01 semantics are unverified. Status:
`RESEARCH_ONLY`, `LITERATURE_SUPPORTED`.

### Laser marking

Candidate: commanded versus measured laser-output stability. KEYENCE documents
built-in thermopile output monitoring during marking. Electrical-current models
remain research-only until source architecture and telemetry are known. Status:
`RESEARCH_ONLY`, `LITERATURE_SUPPORTED`.

### Trim / form

Candidate: stroke-aligned servo load/torque/force profile consistency. Relevant
semiconductor OEM sources document electric/servo cam equipment and 3-5 ton
punch capability. Package geometry, tooling, drive semantics, kinematics, and
reference force remain mandatory. Status: `RESEARCH_ONLY`,
`LITERATURE_SUPPORTED`.

### Singulation

Candidate: SG-specific electromechanical spindle-load consistency. DISCO DAD3660
documents package singulation and spindle-current condition monitoring, but
SG-01 still requires its own telemetry review, fit, envelope, and validation.
WS parameters are never shared. Status: `RESEARCH_ONLY`,
`LITERATURE_SUPPORTED`.

### Final test

Candidate: contact resistance. Keithley guidance supports four-wire sensing,
offset control, current reversal, settling, and contact-local measurement.
Liu et al. show that contact condition matters in wafer-probe testing, but wafer
probes are not final-test sockets. Repository channel names do not prove the
measurement topology. Status: `RESEARCH_ONLY`, `LITERATURE_SUPPORTED`.

Candidate: test-handler motor-signature consistency. DOI
10.1016/j.cie.2026.111872 supplies strong real-semiconductor final-test evidence
using handler motor signatures and downstream DUT electrical results. No
equation is created until motor/current/position/velocity/control semantics are
known. Status: `RESEARCH_ONLY`, `LITERATURE_SUPPORTED`.

## Q. Active runtime research relation

`spindle.current_speed_residual` is active for `wafer_saw` only.

The calibration model is:

`I_expected = a_machine n_actual + b_machine`

The residual is:

`r_I = I_reported - I_expected`

The computation is permitted only when:

- the family is `wafer_saw`;
- calibration and inference refer to the same exact machine;
- the controller and sensor configuration is unchanged;
- current and speed units match exactly;
- timestamps overlap through the unchanged Step 03 alignment path;
- speed is positive, current is nonnegative, and values are finite;
- speed lies inside the robust calibrated range;
- at least three usable samples remain.

What it means: a research indicator of current/load consistency conditional on
speed under calibration assumptions.

What it does not mean: force, wear amount, failure probability, remaining useful
life, causal diagnosis, a safety alarm, or an authoritative maintenance action.

## R. Research-only relations

The following remain visible but are not returned to Step 03:

- wafer-mount dicing-tape tension stability;
- wafer-saw coolant hydraulic resistance;
- die-attach closed-loop force/Z/temperature consistency;
- wire-bond phase-specific ultrasonic-generator electrical-load consistency;
- molding clamp/transfer/temperature consistency;
- commanded/measured laser-output stability;
- trim/form stroke-aligned servo load profile consistency;
- singulation spindle current/speed consistency;
- final-test contact resistance;
- final-test handler motor-signature consistency.

Research-only is not a negative scientific result. It records that the mechanism
could have value but the present measurement/evidence boundary is insufficient
for runtime evidence. Each candidate includes a concrete next experiment rather
than placeholder metadata.

## S. Rejected relations

Two candidates are rejected from the current telemetry architecture:

- Die-attach leak rate: without a controlled isolation event and known volume,
  a live vacuum value has no unique leak-rate meaning.
- Wire-bond ultrasonic impedance: without synchronized voltage/current phase,
  suitable bandwidth, and bond-cycle timing, impedance cannot be reconstructed.

Rejected means the proposed relation cannot be implemented honestly from the
present signals. It does not assert that the underlying physical method is
invalid when properly instrumented.

## T. Instrumentation roadmap

Priority 1 — verify the active spindle path:

- controller documentation for actual speed and reported current;
- independent tachometer and calibrated current reference;
- filter/lag characterization;
- feed, cut depth, material, blade, coolant, temperature, and phase context;
- safe reference load/force and sensor-fault negative controls.

Priority 2 — establish direct high-value measurands:

- Kelvin/contact-isolated voltage/current for final-test contacts;
- differential pressure across a named coolant element;
- actual clamp force and approved projected area;
- actual delivered optical power at a defined plane;
- stroke encoder and actual punch force;
- controlled isolation state and known volume for vacuum leak tests.

Priority 3 — dedicated dynamic acquisition where justified:

- synchronized generator voltage/current/phase and bond trigger for wire bond;
- specified accelerometer axis, mounting, bandwidth, calibration, and
  tachometer/order reference for spindle/blade vibration;
- a dedicated streaming/DSP path for high-rate vibration rather than the
  ordinary low-rate telemetry loop.

Instrumentation must follow the approved PHM data boundary and must not require
unapproved recipes, PPIDs, wafer maps, proprietary geometry, or process windows.

## U. Controlled experiment plans

### Wafer-saw spindle

Use one identified instrumented saw and approved surrogate material. Randomize
and block speed, feed, depth, material, blade state, and safe perturbations.
Calibrate on early healthy blocks; freeze parameters and envelope; validate on
later non-overlapping healthy and seeded-condition blocks. Include no-cut runs,
speed-only changes, current/speed sensor offsets, and thermal repeats. Accept
only stable coefficients, bounded conditioning dependence, predeclared
directional response, and discrimination from sensor faults.

### Final-test contacts

First prove topology with schematics and instrument tracing. Use four-terminal
force/sense connections, current reversal or offset compensation, settled SMU
state, reference resistances, and per-contact fixture identity. Vary current,
contact force, temperature, contamination/wear, and insertion count. Negative
controls change lead/relay/DUT voltage without changing the target contact.

### Wafer-mount web handling

Measure tension, actual torque/current, encoder speed/acceleration, geometry,
and temperature. Apply safe controlled tension changes across motion phases.
Negative controls vary acceleration, friction, and sensor offset at fixed
tension.

### Coolant path

Install calibrated differential-pressure taps around one named element, a
calibrated flow reference, and valve/pump state. Sweep flow, temperature, and
approved restrictions. Negative controls change supply pressure or sensor bias
without changing branch resistance.

### Die-attach vacuum

Run a non-production isolation procedure with known volume, calibrated pressure
time series, valve/pump state, temperature, and reference leaks. Include
outgassing soak, gauge-offset, and incomplete-isolation controls.

### Wire bond

Acquire synchronized high-rate generator voltage/current, phase, bond trigger,
and calibrated vibration reference. Use approved parameter/tool/quality states
with an independent bond-quality outcome. Include electrical gain/phase
injection and no-contact ultrasonic cycles.

### Molding

Use actual clamp-force and cavity-pressure sensors, phase/position, approved
projected area, material and temperature state. Block by material and tool;
include pressure/force bias and area/material negative controls.

### Laser marking

Verify laser architecture and controller mode. Compare internal reported power
with a calibrated optical reference under controlled drive, temperature,
pulse/duty, and optical attenuation. Separate source degradation, downstream
path loss, and power-sensor drift.

### Trim / form

Measure high-rate punch force, current/torque, stroke phase/acceleration, and
mechanism configuration. Vary tool/material/phase safely and include current,
force, acceleration, friction, and temperature controls.

### Singulation

Repeat the spindle study on actual singulation equipment rather than copying
wafer-saw coefficients or evidence. Establish drive semantics and mechanism
equivalence or adopt a different model. Include an independent load/force
reference and specified high-rate vibration acquisition if vibration is studied.

## V. Requirements to advance maturity

To reach `MEASUREMENT_SEMANTICS_VERIFIED`:

- review schematics, controller/OEM definitions, sensor path, unit, sign,
  timing, bandwidth, location, and state semantics;
- verify calibration and traceability state;
- document approved source-ID mapping.

To reach `BENCH_VALIDATED`:

- preregister a controlled protocol;
- use reviewed reference instrumentation;
- separate calibration and validation data;
- pass target, nuisance, and negative-control criteria;
- retain independent artifacts and reviewer sign-off.

To reach `SINGLE_MACHINE_VALIDATED`:

- identify the exact installed machine;
- validate across its intended operating envelope and relevant time periods;
- demonstrate parameter stability, recalibration rules, and sensor-fault handling.

To reach `MULTI_MACHINE_VALIDATED`:

- use at least two real machines of the same justified family;
- evaluate between-machine variation and transfer;
- never silently substitute exact-machine coefficients.

To reach `PROSPECTIVE_PILOT_VALIDATED`:

- freeze the protocol and decision rules before data collection;
- operate observe-only under plant governance;
- use real maintenance outcomes and event-level evaluation;
- measure false alarms, misses, lead time, availability, and human workflow;
- obtain appropriate site, OEM, safety, security, and data-governance approval.

## W. Plant validation and deployment boundary

The present project has no real OSAT fleet failure dataset, prospective plant
pilot, production qualification, calibrated failure probabilities, validated
universal thresholds, OEM-signed physics library, causal diagnostic proof,
production cybersecurity certification, or validated failure-reduction result.

Live-equipment operation in 0.2.5 remains observe-only and research-only.
Physical residuals may contribute research evidence only after the existing
telemetry quality, observability, identity, and provenance gates permit it.
They do not authorize maintenance tickets or machine actions. The deterministic
maintenance layer retains ticket authority; optional RAG/LLM enrichment cannot
create machine state.

A plant study must also distinguish SEMI equipment-state/performance tracking
from PHM evidence. E10/E116-compatible context can help define observation
periods and operating states, but it is not a substitute for reference fault
labels, measurement validation, or prospective outcome evaluation.

## X. State-of-the-art position

Recent reviews by Deng et al. and Khan et al. describe the promise and
limitations of physics-informed learning in PHM/system health. NIST's PHM4SM
program and AMS 100-2 roadmap emphasize measurement science, testbeds, reference
data, performance assessment, verification, validation, and uncertainty. This
supports the project's decision to make evidence maturity and measurement
semantics first-class rather than treating an equation as validated knowledge.

The distinctive useful contribution of Step 01 is modest and architectural:

- it preserves a clean boundary between reviewed physics and statistical
  features;
- it keeps exact-machine calibration separate from machine-family learning;
- it refuses extrapolation;
- it records missing measurements and falsification tests;
- it separates model discrepancy from measurement uncertainty;
- it makes sensor-fault mimicry visible;
- it prevents research candidates from leaking into runtime.

It is not novel physical science, a physical-law discovery system, a validated
diagnostic engine, or a production PHM product. Credibility will come from
metrology and prospective physical evidence, not from increasing the number of
equations.

## Y. Verified bibliography

1. ISO. *Condition monitoring and diagnostics of machine systems — Data
   interpretation and diagnostics techniques — Part 1: General guidelines*.
   ISO 13379-1:2025.
2. ISO. *Condition monitoring and diagnostics of machines — General
   guidelines*. ISO 17359:2018, edition 3; confirmed 2023.
3. ISO. *Quality management — Requirements for measurement management
   systems*. ISO 10012:2026, edition 2.
4. ISO. *Methods for the calibration of vibration and shock transducers —
   Part 21: Vibration calibration by comparison to a reference transducer*.
   ISO 16063-21:2003.
5. ISO. *Mechanical vibration — Measurement and evaluation of machine
   vibration — Part 3: Industrial machinery with a power rating above 15 kW
   and operating speeds between 120 r/min and 30 000 r/min*.
   ISO 20816-3:2022.
6. JCGM. *Evaluation of measurement data — Guide to the expression of
   uncertainty in measurement*. JCGM 100:2008.
   DOI: 10.59161/JCGM100-2008E.
7. JCGM. *International vocabulary of metrology — Basic and general concepts
   and associated terms*, 3rd edition. JCGM 200:2012.
   DOI: 10.59161/JCGM200-2012.
8. JCGM. *Evaluation of measurement data — Supplement 1 to the Guide to the
   expression of uncertainty in measurement — Propagation of distributions
   using a Monte Carlo method*. JCGM 101:2008.
   DOI: 10.59161/JCGM101-2008. No Monte Carlo method is used at runtime.
9. JCGM. *Evaluation of measurement data — Guide to the expression of
   uncertainty in measurement, Amendment 1: Nonlinearity in measurement
   models*. JCGM 100:2008/Amd.1:2026. DOI: 10.59161/PPDI3267.
10. NASA. *Standard for Models and Simulations*. NASA-STD-7009B, 2024.
11. NASA. *NASA Handbook for Models and Simulations: An Implementation Guide
   for NASA-STD-7009B*. NASA-HDBK-7009B, 2026.
12. ASME. *The Role of Uncertainty Quantification in Verification and
   Validation of Computational Solid Mechanics Models*. VVUQ 10.2-2021.
13. NIST. *Prognostics and Health Management for Reliable Operations in Smart
   Manufacturing (PHM4SM)*. Project created 2018; page updated 2025.
14. J. Pellegrino, M. Justiniano, A. Raghunathan, and B. Weiss. *Measurement
   Science Roadmap for Prognostics and Health Management for Smart
   Manufacturing Systems*. NIST AMS 100-2, 2016.
   DOI: 10.6028/NIST.AMS.100-2.
15. S. Khan, T. Yairi, S. Tsutsumi, and S. Nakasuka. “A review of
    physics-based learning for system health management.” *Annual Reviews in
    Control* 57 (2024) 100932. DOI: 10.1016/j.arcontrol.2024.100932.
16. W. Deng, K. T. P. Nguyen, K. Medjaher, C. Gogu, and J. Morio.
    “Physics-informed machine learning in prognostics and health management:
    State of the art and challenges.” *Applied Mathematical Modelling* 124
    (2023) 325–352. DOI: 10.1016/j.apm.2023.07.011.
17. H. Li, Z. Zhang, T. Li, and X. Si. “A review on physics-informed
    data-driven remaining useful life prediction: Challenges and
    opportunities.” *Mechanical Systems and Signal Processing* 209 (2024)
    111120. DOI: 10.1016/j.ymssp.2024.111120.
18. C. Braun, J. Raible, and M. F. Huber. “Physics-Informed Machine Learning
    in Prognostics and Health Management: A Systematic Literature Review.”
    arXiv:2608.10047, submitted 10 August 2026. Final journal publication was
    not verified on the review date; this is cited as a preprint only.
19. M. C. Kennedy and A. O'Hagan. “Bayesian calibration of computer models.”
    *Journal of the Royal Statistical Society Series B* 63(3) (2001) 425–464.
    DOI: 10.1111/1467-9868.00294.
20. J. Brynjarsdóttir and A. O'Hagan. “Learning about physical parameters:
    the importance of model discrepancy.” *Inverse Problems* 30 (2014)
    114007. DOI: 10.1088/0266-5611/30/11/114007.
21. A. Raue, C. Kreutz, T. Maiwald, J. Bachmann, M. Schilling,
    U. Klingmüller, and J. Timmer. “Structural and practical identifiability
    analysis of partially observed dynamical models by exploiting the profile
    likelihood.” *Bioinformatics* 25(15) (2009) 1923–1929.
    DOI: 10.1093/bioinformatics/btp358.
22. P. M. Frank and X. Ding. “Survey of robust residual generation and
    evaluation methods in observer-based fault detection systems.” *Journal
    of Process Control* 7(6) (1997) 403–424.
    DOI: 10.1016/S0959-1524(97)00016-4.
23. I. Weisshaus and O. Y. Licht. *Monitoring system for dicing saws*.
    US6168500B1, 2001.
24. J. Li, D. Li, J. Lin, C. Zhang, and J. Cheng. “Vibration–force coupled
    dynamics and fracture evolution in wafer dicing.” *International Journal
    of Mechanical Sciences* 319 (2026) 111581.
    DOI: 10.1016/j.ijmecsci.2026.111581.
25. DISCO Corporation. *Product Lineup* catalog, 2024. Public catalog includes
    dicing-saw spindle examples at 1.8 kW and 60,000 min⁻¹.
26. maxon. *Motor constants* and *Motor data and simulation*. Technical
    guidance explaining the torque-constant/current relationship.
27. Keithley Instruments / Tektronix. *Low Level Measurements Handbook*,
    7th edition, 2016.
28. Keysight Technologies. *Precise Low Resistance Measurements Using the
    B2961B and 34420A*. Application note 3120-1555.
29. National Instruments. *Best Practice for Using NI SMUs to Test IC in
    Sockets*. Updated 2025.
30. D. S. Liu, M. K. Shih, and W. H. Huang. “Measurement and analysis of
    contact resistance in wafer probe testing.” *Microelectronics Reliability*
    47(7) (2007) 1086–1094. DOI: 10.1016/j.microrel.2006.07.091.
31. C. Branca, P. R. Pagilla, and K. N. Reid. “Governing Equations for Web
    Tension and Web Velocity in the Presence of Nonideal Rollers.” *Journal of
    Dynamic Systems, Measurement, and Control* 135(1) (2013) 011018.
    DOI: 10.1115/1.4007974.
32. S. W. Or, H. L. W. Chan, V. C. Lo, and C. W. Yuen. “Ultrasonic
    wire-bond quality monitoring using piezoelectric sensor.” *Sensors and
    Actuators A* 65(1) (1998) 69–75.
    DOI: 10.1016/S0924-4247(97)01638-5.
33. W. Feng, Q. Meng, Y. Xie, and H. Fan. “Wire bonding quality monitoring
    via refining process of electrical signal from ultrasonic generator.”
    *Mechanical Systems and Signal Processing* 25(3) (2011) 884–900.
    DOI: 10.1016/j.ymssp.2010.09.010.
34. R. Kahle, T. Braun, J. Bauer, K.-F. Becker, M. Schneider-Ramelow, and
    K.-D. Lang. “In-situ measuring module for transfer molding process
    monitoring.” *IMAPS Proceedings* (2016).
    DOI: 10.4071/isom-2016-THA43.
35. B. Kaya, J.-M. Kaiser, K.-F. Becker, T. Braun, and K.-D. Lang. “Process
    Optimization and Implementation of Online Monitoring Process in Transfer
    Molding for Electronic Packaging.” *Journal of Microelectronics and
    Electronic Packaging* (2019). DOI: 10.4071/IMAPS.954402.
36. R. Borràs, J. del Río Fernández, C. Oriach, and J. Juliachs. “Laser
    diodes optical output power model.” *Measurement* 133 (2019) 56–67.
    DOI: 10.1016/j.measurement.2018.10.007.
37. KEYENCE America. Laser marking resources describing built-in thermopile
    power monitoring for detecting output-power drops. Accessed 2026-08-31.
38. TRUMPF. *Condition Monitoring for lasers and laser systems*. Accessed
    2026-08-31.
39. Leybold. *Fundamentals of Leak Detection: Pressure rise and pressure drop
    tests*. Technical reference.
40. SEMI. *Specification for Definition and Measurement of Equipment
    Reliability, Availability, and Maintainability (RAM) and Utilization*.
    SEMI E10-0422, current.
41. SEMI. *Automated Reliability, Availability, and Maintainability Standard
    (ARAMS): Concepts, Behavior, and Services*. SEMI E58-0703, inactive.
42. SEMI. *Specification for Equipment Performance Tracking*. SEMI E116.
43. Y. Wang, Z. Li, F. Chen, and Z. Xu. “Processing Characteristics of
    Ultra-Precision Cutting of 4H-SiC Wafers by Dicing Blade.”
    *Micromachines* 17(2) (2026) 187.
    DOI: 10.3390/mi17020187. The public article reports current/speed
    experiments but no separate machine-readable raw trace was found.
44. W. Leitgeb, D. Brunner, and L. Ferlan / Infineon Technologies AG.
    *Method and device for monitoring a dicing tape tension*.
    EP3705862B1 / US20200286795A1.
45. DISCO Corporation. *DAD3660 Automatic Dicing Saw* product information,
    including package singulation and spindle-current condition monitoring.
46. Besi. *9800 TC next* product information, including bond force, bond-head Z,
    thermal control, bond traces, and inline process monitoring.
47. C. T. Wu, S. H. Li, and C. S. Tsou. “Integrating FDC and Machine Learning
    for Enhanced Anomaly Detection in WB Bonding Joint Quality.” *Computer
    Modeling in Engineering & Sciences* 88(1) (2026) 96.
    DOI: 10.32604/cmc.2026.078762.
48. Besi. *Fico Molding Line* product information, including active/dynamic
    clamp force, transfer pressure, multi-zone temperature, and cavity vacuum.
49. Gallant Micro Machining Co. *SP Series Trim & Form Equipment* product page;
    electric cam servo and stated tonnage capability.
50. Guangdong Taijin Semiconductor Technology. *Auto Trim/Form System* product
    page; 3-5 ton servo-motor punch capability.
51. L. A. A. Roy, J. S. B. Beh, C. K. Yeo, and S. Regunathan.
    “Process-aware graph-temporal framework for equipment prognostics with
    multimodal data at semiconductor final test.” *Computers & Industrial
    Engineering* 214 (2026) 111872. DOI: 10.1016/j.cie.2026.111872.
52. STMicroelectronics. *ST Dataset for Automatic Wafer Fault Detection*.
    Official repository: https://github.com/STMicroelectronics/ST-AWFD.
53. L. Rennpferdt, S. Bohne, and H. K. Trieu. *Optical Profilometer Dataset for
    Diced Surfaces Obtained with Wafer Dicing Machine at Varying Feed
    Velocities*. DOI: 10.15480/882.15763.
54. X. Xie et al. *DIFFUMA: High-Fidelity Spatio-Temporal Video Prediction via
    Dual-Path Mamba and Diffusion Enhancement*. arXiv:2507.06738 (CHDL).
55. T. N. da C. Fernandes. *Implementação de manutenção preditiva numa indústria
    de semicondutores*. ISEP master's dissertation, hdl:10400.22/20698.
56. UTAC Group. *Sustainability Report 2023*; corporate industrial-practice
    evidence for DISCO wafer saw logs, FDC/data mining and predictive maintenance.
57. C.-C. Hsu. *AOI-Based Defect Detection in the Wire Bonding Process*.
    National Sun Yat-sen University thesis record `etd-0609125-111038` (2025).
    The full thesis is embargoed until 2035; no public sample count is assigned.
58. C.-C. Hsu et al. *Progressive Alignment with VLM-LLM Feature to Augment
    Defect Classification for the ASE Dataset*. arXiv:2404.05183; IEEE ICCE
    2025 DOI 10.1109/ICCE63647.2025.10930135. The separate drilling/AOI dataset
    reports 455 samples and is not wire-bond telemetry.

This bibliography records sources actually used to bound claims. Listing a
standard or publication does not claim compliance, endorsement, or validation
of OSAT Fleet Command.
