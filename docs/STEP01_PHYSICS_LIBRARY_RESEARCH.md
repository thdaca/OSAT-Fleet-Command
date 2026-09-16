# Step 01 Physics / Engineering Library Research Review

## 1. Purpose

Step 01 turns engineering knowledge into small executable claims. Its purpose is
not to maximize feature count. Its purpose is to decide, before a quantity can
influence the PHM path, whether the mechanism, measurements, units, operating
envelope, hidden variables, uncertainty, and falsification experiment are
defensible.

This document is the research basis for OSAT Fleet Command 0.2.1. The build is a
research/development teaching system. It is not production qualified, does not
claim causal diagnosis, and has not been validated on a real OSAT fleet. A
relation marked `RUNTIME` is approved only for the existing research runtime and
inside its stated conditions. That status is not an OEM endorsement or a claim
that the relation is plant-ready.

The central educational principle is:

> A physics relation is an executable scientific claim, not merely an algebraic
> feature.

Rejected relations are therefore a positive result. They show where literature
suggests a useful mechanism but current telemetry does not measure the variables
needed to execute it honestly.

## 2. Research method

### 2.1 Review type and date

This was a **structured engineering literature review**, not a formal systematic
review. Searches were performed on 2026-08-31. The review was bounded to the nine
machine families and the telemetry already approved in `machines.py`.

### 2.2 Sources consulted

Search and verification used:

- publisher records and abstracts at ScienceDirect;
- arXiv metadata and full preprint records;
- ISO's official standards catalog;
- BIPM/JCGM official metrology guides;
- ASME's official VVUQ catalog;
- NASA's official standards catalog and public handbook;
- Google Patents for the full dicing-saw patent record;
- NIST/NBS measurement references;
- manufacturer technical documentation from NI, Keysight, Texas Instruments,
  and Leybold;
- the U.S. Army Corps of Engineers publication library;
- Fraunhofer publication records for semiconductor transfer molding; and
- DOI/publisher metadata for the cited wire-bond, laser, dicing, and molding
  studies.

Example search strings included:

- `physics informed machine learning prognostics health management review`;
- `wafer dicing spindle current load monitoring`;
- `wafer dicing vibration force coupled dynamics`;
- `motor torque constant current Kt application note`;
- `ultrasonic wire bonding electrical impedance monitoring`;
- `wire bonding ultrasonic generator voltage current harmonics`;
- `laser diode optical output current temperature model`;
- `IC test socket contact resistance degradation`;
- `low resistance measurement current floor four wire thermal EMF`;
- `transfer molding semiconductor cavity pressure in situ monitoring`;
- `vacuum leak rate pressure rise volume`; and
- `Darcy Weisbach pressure drop flow friction factor hydraulic diameter`.

### 2.3 Inclusion and exclusion rules

Sources were preferred in this order: standards and metrology guidance,
peer-reviewed primary studies, peer-reviewed reviews, official manufacturer or
equipment documentation, semiconductor application notes, patents, then
recognized technical references. A runtime mechanism needed a primary,
first-principles, or authoritative equipment basis; a review alone was not
treated as equipment validation.

Sources were included only when their title, organization/authors where
practical, year, and DOI/standard/patent/document identifier could be checked.
Random blogs, marketing claims, unsourced summaries, forum anecdotes, and
AI-generated text were excluded. No source was used to infer a proprietary
recipe, wafer map, customer process window, or confidential OEM constant.

Several relevant articles were available only through publisher metadata and
abstracts. In particular, the 2026 dicing-dynamics article and some conference
records were not treated as if their full derivations had been reviewed. The
code cites only the limited proposition visible in the verified record. Current
commercial ADT/DISCO service manuals were not located in a legally accessible,
public form and are not represented as reviewed evidence.

### 2.4 Decision process

For each family the review followed the same sequence:

1. enumerate the approved channels and units;
2. identify a plausible mechanism;
3. locate evidence for the mechanism;
4. map every equation variable to a measured channel;
5. identify unmeasured dominant variables and measurement-semantic ambiguity;
6. classify parameters as universal, machine-fitted, assumed, or unknown;
7. define operating limits, numerical guards, uncertainty sources, and a
   falsification experiment; and
8. mark the claim `RUNTIME`, `RESEARCH_ONLY`, or `REJECTED`.

The review did not score papers or claim exhaustive coverage. A future release
should repeat the search with institutionally licensed databases and an
equipment expert for each family.

## 3. Physics-informed PHM state of the art

Deng et al. organize physics-informed PHM by the form of knowledge and the point
where it is introduced. Li et al. group physics-informed data-driven RUL work
into physical-model/data fusion, stochastic degradation models, and PIML.
Braun, Raible, and Huber review 212 studies using observational, inductive,
learning, and hybrid biases. Taken together, the literature shows several broad
integration patterns:

- **Data/input level:** physical quantities, residuals, simulated data, and
  mechanistically selected features are supplied to a statistical learner.
- **Architecture level:** model structure, state variables, graph structure, or
  differential-equation components encode prior knowledge.
- **Loss/constraint level:** conservation, monotonicity, boundary conditions, or
  other constraints penalize physically inconsistent learning.
- **Hybrid/model fusion:** a physical model and data-driven correction or
  discrepancy model contribute jointly.
- **Residual/model-based diagnosis:** measured behavior is compared with a
  reference model, with residuals interpreted under an explicit fault and
  operating-condition hypothesis.

The same reviews identify unresolved problems: incomplete physics, sparse
failure evidence, model discrepancy, uncertainty, changing operating regimes,
transfer across machines, and interpretability that is often asserted more
strongly than demonstrated. Braun et al. also report concentration on batteries
and bearings and a large share of problem-specific solutions. That limits what
can be inferred for OSAT equipment.

Step 01 uses the conservative data/input and residual route. It does not add a
neural architecture, physics-constrained loss, symbolic discovery, or universal
equation library. The scientific contribution sought here is traceability from
source to mechanism to telemetry to executable test—not model sophistication.

ISO 13379-1:2025 supplies general diagnostic-development guidance, while JCGM,
ASME VVUQ, and NASA model-credibility documents emphasize explicit measurands,
uncertainty sources, intended use, model-form limitations, and validation.
Those documents informed the review gate. The project does not claim compliance
with any of them.

## 4. What OSAT Fleet Command Step 01 does

The implementation contains three deliberately small concepts:

- `ResearchReference`: verified short provenance stating exactly what a source
  supports;
- `PhysicsRelation`: an executable runtime computation plus mechanism,
  assumptions, validity/invalidity conditions, confounders, calibration,
  identifiability, uncertainty, sensitivity, cross-sensitivity,
  instrumentation gaps, and falsification tests; and
- `ResearchCandidate`: a documented relation that is scientifically plausible
  or considered-and-rejected but cannot execute with current evidence.

`RelationKind` prevents epistemic overstatement:

- `FIRST_PRINCIPLES` is a direct law or conservation statement;
- `CONSTITUTIVE` is an established relation conditional on system/material
  properties;
- `SEMI_EMPIRICAL` has physical structure and fitted parameters;
- `MACHINE_FITTED` has a mechanistic structure whose parameters belong to the
  exact machine; and
- `DIAGNOSTIC_PROXY` is supported as an indicator but is not a direct law.

`relations_for_family()` exposes only `RUNTIME` records. Step 03 is unchanged and
cannot see research-only or rejected candidates. `research_catalog_for_family()`
exists solely for student/research inspection. `audit_physics_library()` checks
record consistency without creating a configuration framework.

The runtime computations remain deterministic, vectorized, offline, and O(n) in
window length. No network, symbolic solver, Monte Carlo inference, model search,
or LLM is involved.

## 5. Relation acceptance gate

A relation is runtime-enabled only when every applicable gate is satisfied.

### Gate A — mechanism

There must be a defensible physical or engineering mechanism. Correlation and
dimensional validity by themselves are insufficient.

### Gate B — measurement semantics

Channel meanings must correspond to equation variables. A channel called
`pressure` is not automatically differential pressure; a current channel is not
automatically torque.

### Gate C — units

Every input unit and output unit must be explicit and dimensionally sensible.

### Gate D — observability

Dominant variables must be measured or defensibly stable within a narrow
declared regime. If an omitted variable can dominate, the relation is not
runtime-ready.

### Gate E — identifiability

Fitted parameters require enough independent excitation. A regression slope on
constant input is not an identified parameter.

### Gate F — operating envelope

Startup, steady processing, reversal, material class, controller mode, and other
conditions that bound use must be stated.

### Gate G — confounders

Alternative causes of residual movement must be recorded. Sensitivity is not
specificity.

### Gate H — numerical robustness

The implementation must control division by zero, non-finite input, overflow,
outliers, extrapolation, and degenerate fitting.

### Gate I — evidence

At least one high-quality source must support the actual mechanism claimed. An
equipment patent can document one implementation; it cannot establish a
universal relation for every machine.

### Gate J — falsifiability

A concrete controlled experiment must be able to invalidate the relation.

Passing the gate means “usable as research evidence within the declared
runtime,” not “validated diagnostic.”

## 6. Machine-family research matrix

### 6.1 Wafer mount

- **Existing telemetry:** vacuum pressure [kPa], roller motor current [A], roller
  temperature [°C], arm tracking error [µm], optional web tension [N].
- **Mechanism investigated:** motor current → torque → roller tangential force →
  web tension.
- **Candidate:** `T_web ≈ f(I, Kt, radius, transmission, acceleration, friction,
  phase)`.
- **Missing variables:** torque constant, radius, gearing, acceleration, motion
  phase, friction state, and drive-current semantics.
- **Evidence:** manufacturer motor documentation supports torque constant, not
  this machine's force mapping.
- **Status:** `RESEARCH_ONLY`.
- **Rationale:** current and tension are both present, but an unconstrained fit
  would mix dynamics and friction and would be correlation rather than a torque
  balance.

### 6.2 Wafer saw / dicing

- **Existing telemetry:** spindle current [A], speed [RPM], vibration [mm/s],
  coolant pressure [MPa], flow [L/min], temperature [°C], feed-axis error [µm].
- **Mechanisms investigated:** electromechanical load consistency; hydraulic
  pressure-loss/flow behavior.
- **Candidates:** `I - (b + m·speed)` and Darcy–Weisbach-type `Δp(Q)`.
- **Missing variables:** feed rate, depth, kerf, blade diameter/wear, material,
  controller state; for coolant, differential pressure, geometry, properties,
  pump and valve state.
- **Evidence:** US6168500B1 documents spindle feedback current used as dicing
  load signal; motor documentation supports current/torque coupling; the 2026
  dicing abstract documents richer vibration/force/fracture dynamics; USACE
  guidance documents required hydraulic variables.
- **Status:** spindle residual `RUNTIME`; coolant relation `RESEARCH_ONLY`.
- **Rationale:** the spindle claim is deliberately limited to exact-machine
  electromechanical consistency. The pressure channel cannot presently be
  interpreted as a known pressure drop.

### 6.3 Die attach

- **Existing telemetry:** nozzle vacuum [kPa], z-axis current [A], position error
  [µm], stage temperature [°C], settle time [ms].
- **Mechanism investigated:** isolated-volume pressure rise for vacuum leakage.
- **Candidate:** `qL = V·Δp/Δt`.
- **Missing variables:** known volume, isolation/valve/pump state, a defined
  pressure-rise interval, flow, and gas temperature.
- **Evidence:** Leybold's vacuum reference supports the equation and explicitly
  warns about outgassing/virtual leaks.
- **Status:** `REJECTED` for current instrumentation.
- **Rationale:** one running vacuum value cannot identify leakage or separate it
  from commanded pneumatics and pickup state.

### 6.4 Wire bond

- **Existing telemetry:** bond force [gf], bond-head current [A], ultrasonic
  current [mA], frequency shift [Hz], clamp temperature [°C].
- **Mechanism investigated:** transducer/bond interaction changes mechanical
  vibration and electrical input impedance/harmonics.
- **Candidate:** complex/time-frequency `Z = V/I` plus vibration/harmonic
  features.
- **Missing variables:** ultrasonic voltage, voltage-current phase, waveform
  bandwidth, bond-cycle phase, transducer amplitude, and harmonics.
- **Evidence:** Or et al. use a dedicated PZT sensor; Feng et al. acquire both
  voltage and current and resolve harmonics/phases; Zhang et al. use real and
  imaginary input impedance.
- **Status:** `REJECTED` for current instrumentation.
- **Rationale:** current plus low-rate frequency shift cannot reconstruct
  impedance. Inventing impedance would contradict the cited methods.

### 6.5 Molding

- **Existing telemetry:** cavity pressure [bar], transfer motor current [A], mold
  temperature [°C], clamp pressure [bar], plunger position error [mm].
- **Mechanism investigated:** cavity-pressure × projected-area force opposed by
  clamp force through fill, pack, and cure.
- **Candidate:** `F_required(t) = p_cavity(t)·A_projected` with dynamic/material
  corrections.
- **Missing variables:** actual clamp force, cylinder/transmission geometry,
  projected area, process phase, true plunger position, resin rheology and cure.
- **Evidence:** semiconductor transfer-molding studies use in-cavity pressure,
  tool/melt-front temperature, transfer speed, material condition, and
  dielectric cure data; machine settings are not equivalent to in-cavity state.
- **Status:** `REJECTED`.
- **Rationale:** a simple pressure ratio would be unsupported, and some geometry
  may be protected process information that Step 01 must not ingest.

### 6.6 Laser marking

- **Existing telemetry:** delivered laser power [W], drive current [A], laser
  temperature [°C], galvo current [A], tracking error [µrad].
- **Mechanism investigated:** above-threshold laser-diode output with
  temperature-dependent threshold current and slope efficiency.
- **Candidate:** `Pout ≈ ηs(T)·max(I-Ith(T),0)`.
- **Missing variables:** verified laser architecture, junction temperature,
  internal feedback/controller state, duty cycle/Q-switch state, optical losses.
- **Evidence:** Borràs et al. model diode optical output versus current and
  temperature and discuss feedback-controlled output.
- **Status:** `RESEARCH_ONLY`.
- **Rationale:** the marker may be fiber, pulsed/Q-switched, or closed-loop; the
  generic diode relation cannot be assigned to an unknown source architecture.

### 6.7 Trim / form

- **Existing telemetry:** punch force [kN], press motor current [A], die vibration
  [mm/s], tracking error [µm], die temperature [°C].
- **Mechanism investigated:** motor current → torque → transmission/linkage →
  punch force by stroke phase.
- **Candidate:** `F(θ) ≈ Kt·I·G·mechanical_advantage(θ)/losses`.
- **Missing variables:** Kt, gearing, linkage geometry, stroke phase,
  acceleration, friction/losses, synchronized high-rate force/current.
- **Evidence:** manufacturer motor documentation supports only the first
  current-to-torque link.
- **Status:** `RESEARCH_ONLY`.
- **Rationale:** force is measured, which makes a controlled experiment possible,
  but a single unphased fit would mix inertia, tooling, and friction.

### 6.8 Singulation

- **Existing telemetry:** blade vibration [mm/s], spindle current [A], optional
  speed [RPM], coolant flow [L/min], feed-position error [µm].
- **Mechanisms investigated:** exact-machine spindle load consistency; coupled
  blade vibration/load dynamics.
- **Candidates:** current-speed residual; high-rate vibration/load model.
- **Missing variables:** feed, depth, blade/material state, controller state; for
  dynamics, sensor bandwidth/axis, tachometer/order reference, high-rate data.
- **Evidence:** motor/load and dicing dynamics sources support the limited
  mechanisms, not a transferable force equation.
- **Status:** spindle residual `RUNTIME`; dynamic vibration relation
  `RESEARCH_ONLY`.
- **Rationale:** the low-rate scalar vibration channel cannot support the
  spectral/dynamic model. Such work belongs on a dedicated DSP path.

### 6.9 Final test

- **Existing telemetry:** contact voltage drop [mV], site current [A], socket
  temperature [°C], handler current [A], handler vibration [g].
- **Mechanisms investigated:** Ohmic path resistance; contact-path dissipation.
- **Candidates:** `R[mΩ] = median(V[mV]/I[A])`; `P[mW] = V[mV]·I[A]`.
- **Missing variables:** Kelvin topology, contact-only voltage, relay/lead/DUT
  separation, contact force, insertion count, settling state, per-pin identity.
- **Evidence:** NIST/NBS supports resistance measurement principles; Keysight
  documents low-resistance safeguards; NI documents socket spring-pin wear,
  debris, and intermittency.
- **Status:** resistance `RUNTIME`; power `RESEARCH_ONLY`.
- **Rationale:** resistance is more directly connected to series-path change and
  removes commanded current magnitude from the feature. Power remains valid
  algebra but is less direct and strongly current-dependent.

## 7. Active runtime relations

### 7.1 `spindle.current_speed_residual`

**Families:** wafer saw and singulation.

**Interpretation:** an exact-machine electromechanical spindle-load consistency
residual conditioned on speed. It is not cutting force, blade force, failure
probability, or causal diagnosis.

The healthy calibration model is:

```text
I_expected[A] = b_machine[A] + m_machine[A/RPM] × speed[RPM]
I_residual[A] = median(I_measured - I_expected)
```

The linear structure is mechanistically motivated by motor current/load behavior
and dicing equipment evidence, but both coefficients are machine-fitted. They
are not universal torque or cutting-force constants.

**Numerical and calibration safeguards:**

- at least 20 finite, positive-speed, non-negative-current samples;
- 5th–95th percentile speed span of at least 100 RPM and 0.2% of median speed;
- centered/scaled speed for numerical conditioning;
- Huber robust regression for moderate current outliers;
- finite coefficient/residual checks; and
- median/MAD residual scale recorded with a numerical floor. The scale is not a
  confidence interval or health threshold.

The robust span is important. One extreme speed sample cannot make a
constant-speed dataset identifiable. A fit with insufficient excitation fails
clearly.

**Known:** motor torque can relate to current under known motor/controller
conditions; a dicing-saw design uses feedback current as a load signal; dicing
forces interact with richer process and vibration variables.

**Assumed:** the channels mean drive/load-current magnitude and true spindle
speed; intervals are steady processing; omitted process variables are stable
enough for comparison; current/speed controller semantics have not changed.

**Fitted:** slope, intercept, robust residual scale, and observed healthy speed
span belong to the exact installed machine.

**Unknown:** feed, depth, kerf, blade condition/geometry, material, controller
state, and calibrated torque/force mapping.

**Sensitivity:** positive movement can accompany increased load, friction,
clogging, blade wear, or bearing load. **Specificity is low:** material, feed,
depth, coolant, acceleration, controller changes, and current-sensor bias can
move the same residual.

**Falsification:** repeat controlled healthy runs across speed. If the relation
is not stable, or if controlled load changes at fixed speed do not move the
residual consistently, deactivate it for that equipment. A motor/drive or
controller change invalidates calibration until re-tested.

### 7.2 `contacts.contact_resistance`

**Family:** final test.

**Interpretation:** an aggregate aligned positive resistance of the measured
contact path. It is not necessarily the resistance of a single spring pin and is
not a specific diagnosis of contamination, wear, or misalignment.

```text
R_sample[mΩ] = V_drop[mV] / I_site[A]
R_output[mΩ] = median(valid aligned R_sample)
```

The unit follows directly because 1 mV / 1 A = 1 mΩ. Median of aligned sample
ratios is used rather than ratio of medians so voltage and current from different
operating instants are not combined. The median also limits isolated contact
bounce/outlier influence.

**Numerical safeguards:** current must exceed the larger of 1 µA and 0.1% of the
window's 90th-percentile absolute current. This is explicitly a numerical and
measurement-resolution guard, not a production health limit. At least three and
at least half of the finite paired samples must remain. Voltage/current polarity
must imply non-negative passive resistance. NaN, infinity, division singularity,
and overflow cannot emit a finite-looking relation output.

**Known:** Ohm's law supports V/I; socket wear, debris, and intermittent pins can
affect connectivity; precision low-resistance measurement requires adequate
current, synchronization, offset control, and preferably Kelvin sensing.

**Assumed:** voltage and current refer to one path and interval, polarity is
consistent, the interval is settled, and other series drops remain fixed enough
for comparison.

**Fitted:** no equation coefficient. A real deployment still needs an
exact-fixture reference distribution and repeatability study; downstream exact
machine modeling handles the reference, not Step 01.

**Unknown:** whether sensing is Kelvin, how much relay/lead/DUT voltage is
included, per-pin identity, contact force, insertion count, and source-settling
state.

**Sensitivity:** a sustained positive shift can accompany increasing series
resistance or less repeatable contacts. **Specificity is low:** relay, lead, DUT,
temperature, range, timing, offset, and fixture changes can produce the same
shift. Intermittent opens can instead reduce usable samples.

**Falsification:** repeat known-good contacts under controlled current and
temperature and compare with a traceable/four-wire reference. Deactivate the
indicator if repeatability is poor, controlled resistance changes are not
recovered, or other series elements dominate.

## 8. Research-only relations

### Wafer-mount roller current / web tension

The current-to-torque mechanism is plausible and both current and tension are
available. Activation waits for motion phase, acceleration, drive semantics,
transmission/roller geometry, and a controlled tension experiment.

### Wafer-saw coolant hydraulic resistance

The old `median(pressure)/median(flow)` runtime feature was removed. A valid
hydraulic model needs a pressure **drop** across a named element plus geometry,
fluid/regime information, and valve/pump state. `coolant_pressure` does not state
sensor location or differential semantics.

### Laser output / current / temperature

The diode relation is supported for characterized diode devices. Activation
waits for confirmation that this marker uses that architecture and for controller
mode, pulse/duty-cycle, junction-temperature, and optical-reference data.

### Trim/form current / punch force

Measured punch force makes future calibration possible, but stroke phase,
linkage, torque constant, acceleration, and friction are needed before the fit
has mechanical meaning.

### Singulation vibration / load dynamics

Dynamic vibration-force work requires defined high-rate sensor bandwidth,
mounting/axis, order reference, and process context. The ordinary low-rate
telemetry path is intentionally not converted into a speculative FFT feature.

### Final-test contact dissipation power

`mV × A = mW` is dimensionally correct, but power is strongly driven by commanded
current and less direct for contact degradation than resistance. It remains an
experimental thermal quantity and cannot enter Step 03.

## 9. Rejected relations and instrumentation gaps

### Die-attach nozzle leak rate

Rejected because `nozzle_vacuum` alone does not provide known volume,
isolation/valve/pump state, or a controlled `Δp/Δt`. Needed: a known isolated
volume, event/valve state, calibrated rate-of-rise acquisition, temperature, and
ideally flow/reference leak. A single vacuum value must not be labeled leak
rate.

### Wire-bond ultrasonic impedance

Rejected because current plus frequency shift cannot yield complex impedance or
the published waveform/harmonic features. Needed: synchronized ultrasonic
voltage and current waveforms, phase, sufficient bandwidth, bond-cycle trigger,
and optionally a calibrated PZT vibration channel.

### Molding clamp/cavity force balance

Rejected because hydraulic pressure is not actual clamp force without cylinder
geometry/losses, and cavity behavior is phase/material/cure dependent. Needed:
actual force, phase/position, approved projected area, and in-cavity/cure
instrumentation. If that requires proprietary package geometry or recipe data,
the relation remains outside this equipment-health library.

These records demonstrate a crucial boundary: useful literature plus
insufficient telemetry equals no runtime relation.

## 10. Uncertainty and model discrepancy

JCGM 100 begins with a well-defined measurand and an uncertainty model. JCGM 101
provides Monte Carlo propagation when input probability distributions and the
measurement model are justified. Those prerequisites are not present here:
sensor calibration certificates, covariance, resolution models, and validated
input distributions are absent. Step 01 therefore documents uncertainty
**sources** and does not manufacture numerical confidence intervals.

Relevant uncertainty sources include:

- measurement accuracy, calibration drift, quantization, offsets, and range;
- timestamp alignment and source/settling timing;
- finite calibration data and fitted-parameter uncertainty;
- operating-condition uncertainty;
- omitted variables; and
- model-form discrepancy.

Measurement noise and model discrepancy are different. A residual can change
because the machine degraded, the operating regime changed, a sensor drifted,
or the model assumption stopped representing the machine. Robust statistics
reduce some outlier sensitivity but do not resolve those explanations.

ASME VVUQ 10.2 distinguishes model-form, input, numerical, and basis-data
uncertainty and emphasizes validation experiments. NASA-HDBK-7009B emphasizes
intended/permissible use, assumptions, and evidence for model credibility. Step
01 adopts those habits at small scale; it is not a computational solid mechanics
model and does not claim compliance.

## 11. Novelty and differentiation assessment

The PHM/PIML literature already includes physics-informed features, residuals,
hybrid models, constraints, uncertainty-aware approaches, and model-based
diagnosis. Semiconductor literature already includes spindle-current load
monitoring, wire-bond electrical/vibration monitoring, transfer-mold in-situ
sensing, laser output models, and contact-resistance measurement practice.
None of those mechanisms is claimed as new here.

The implementation emphasizes a pedagogical combination that is not always
visible in small PHM examples: source-scoped claims, epistemic type, an explicit
activation gate, machine identifiability, measurement semantics, numerical
guards, uncertainty sources, falsification, and first-class rejected candidates.
The review did not establish that this combination is unique, first, or beyond
published practice.

**Novelty has not been established.** This implementation combines several
established model-credibility practices into a lightweight PHM relation library.

What remains unproven includes predictive utility on real OSAT failures,
transfer across vendors or machines, calibrated uncertainty, fault specificity,
threshold validity, maintenance impact, and prospective plant performance.

## 12. Experiments required for real validation

### Spindle electromechanical load residual

1. Verify source semantics, units, sample timing, drive/controller mode, and
   whether current is torque-producing/feedback load current.
2. On one exact machine, collect repeated healthy steady cuts across the allowed
   speed envelope while controlling or recording feed, depth, kerf, blade,
   material, coolant, acceleration, and controller state.
3. Use a calibrated torque/force reference where feasible. Apply controlled load
   changes at fixed speed and verify residual direction and repeatability.
4. Repeat across days, blade changes, maintenance, and environmental conditions
   to quantify parameter stability, measurement uncertainty, and model
   discrepancy.
5. Introduce safe known mechanical/process changes under engineering approval;
   measure sensitivity and false response to confounders separately.
6. Repeat on multiple wafer saws and singulation tools. Do not share exact-machine
   coefficients. Test whether even the relation structure transfers.
7. Pre-register pass/fail criteria before allowing live health influence.

### Contact-path resistance

1. Document the actual voltage/current topology, polarity, range, settling,
   relays/leads, DUT contribution, and whether sensing is Kelvin.
2. Compare the telemetry-derived value with traceable low-resistance standards
   and a synchronized four-wire reference across the intended current range.
3. Repeat known-good insertions over temperature and time to quantify
   repeatability, thermal EMF, offsets, bounce, and contact-to-contact variation.
4. Introduce controlled resistance and known socket conditions (cleaning,
   contamination surrogate, worn pin, misalignment) without inferring that any
   one condition is uniquely diagnosed.
5. Vary fixture, relay, DUT, current, and temperature independently to measure
   cross-sensitivity and identify the actual measurand.
6. Determine how intermittent opens should affect data quality/observability
   rather than forcing a resistance value.
7. Validate on multiple sockets/testers with separate exact-machine references
   before any maintenance use.

No synthetic demo result substitutes for these experiments.

## 13. Full bibliography

1. W. Deng, K. T. P. Nguyen, K. Medjaher, C. Gogu, and J. Morio,
   “Physics-informed machine learning in prognostics and health management:
   State of the art and challenges,” *Applied Mathematical Modelling*, vol. 124,
   pp. 325–352, 2023. DOI: `10.1016/j.apm.2023.07.011`.

2. H. Li, Z. Zhang, T. Li, and X. Si, “A review on physics-informed data-driven
   remaining useful life prediction: Challenges and opportunities,” *Mechanical
   Systems and Signal Processing*, vol. 209, art. 111120, 2024. DOI:
   `10.1016/j.ymssp.2024.111120`.

3. C. Braun, J. Raible, and M. F. Huber, “Physics-Informed Machine Learning in
   Prognostics and Health Management: A Systematic Literature Review,” 2026.
   Identifier: `arXiv:2608.10047`. Preprint status is explicit.

4. International Organization for Standardization, *Condition monitoring and
   diagnostics of machine systems — Data interpretation and diagnostics
   techniques — Part 1: General guidelines*, 2nd ed., 2025. Standard:
   `ISO 13379-1:2025`.

5. Joint Committee for Guides in Metrology, *Evaluation of measurement data —
   Guide to the expression of uncertainty in measurement*, 2008. DOI:
   `10.59161/JCGM100-2008E`.

6. Joint Committee for Guides in Metrology, *Supplement 1 to the Guide to the
   expression of uncertainty in measurement — Propagation of distributions
   using a Monte Carlo method*, 2008. DOI: `10.59161/JCGM101-2008`.

7. American Society of Mechanical Engineers, *The Role of Uncertainty
   Quantification in Verification and Validation of Computational Solid
   Mechanics Models*, 2021. Standard: `ASME VVUQ 10.2-2021`.

8. National Aeronautics and Space Administration, *NASA Handbook for Models and
   Simulations: An Implementation Guide for NASA-STD-7009B*, 2026. Identifier:
   `NASA-HDBK-7009B`.

9. I. Weisshaus and O. Y. Licht, “Monitoring system for dicing saws,” United
   States patent, issued 2001. Patent: `US6168500B1`.

10. J. Li, D. Li, J. Lin, C. Zhang, and J. Cheng, “Vibration–force coupled
    dynamics and fracture evolution in wafer dicing,” *International Journal of
    Mechanical Sciences*, vol. 319, art. 111581, 2026. DOI:
    `10.1016/j.ijmecsci.2026.111581`. Review access was limited to publisher
    metadata/abstract.

11. Unitrode/Texas Instruments, “How to Measure Kt and Kv Without Measuring
    Torque or Angular Velocity,” Application Note U-105, legacy undated
    application note. Identifier: `TI/Unitrode U-105`.

12. S. W. Or, H. L. W. Chan, V. C. Lo, and C. W. Yuen, “Ultrasonic wire-bond
    quality monitoring using piezoelectric sensor,” *Sensors and Actuators A:
    Physical*, vol. 65, no. 1, pp. 69–75, 1998. DOI:
    `10.1016/S0924-4247(97)01638-5`.

13. W. Feng, Q. Meng, Y. Xie, and H. Fan, “Wire bonding quality monitoring via
    refining process of electrical signal from ultrasonic generator,”
    *Mechanical Systems and Signal Processing*, vol. 25, no. 3, pp. 884–900,
    2011. DOI: `10.1016/j.ymssp.2010.09.010`.

14. D. Zhang, S. Ling, S. Yi, and S. W. Foo, “Improved monitoring of ultrasonic
    wire bonding via input electrical impedance,” *Proceedings of the 6th
    Electronics Packaging Technology Conference*, 2004. DOI:
    `10.1109/EPTC.2004.1396634`. Review access was limited to verified
    metadata/abstract.

15. R. Borràs, J. del Río Fernández, C. Oriach, and J. Juliachs, “Laser diodes
    optical output power model,” *Measurement*, vol. 133, pp. 56–67, 2019. DOI:
    `10.1016/j.measurement.2018.10.007`.

16. R. Kahle, T. Braun, J. Bauer, K.-F. Becker, M. Schneider-Ramelow, and K.-D.
    Lang, “In-situ measuring module for transfer molding process monitoring,”
    *IMAPS Proceedings of the International Symposium on Microelectronics*,
    2016. DOI: `10.4071/isom-2016-THA43`.

17. B. Kaya, J.-M. Kaiser, K.-F. Becker, T. Braun, and K.-D. Lang, “Process
    optimization and implementation of online monitoring process in transfer
    molding for electronic packaging,” *Journal of Microelectronics and
    Electronic Packaging*, 2019. DOI: `10.4071/IMAPS.954402`.

18. National Instruments, “Best Practice for Using NI SMUs to Test IC in
    Sockets,” updated 2025. Identifier: NI supplemental technical document.

19. Keysight Technologies, *Precise Low Resistance Measurements Using the B2961B
    and 34420A*, undated application note, accessed 2026. Document:
    `Keysight 3120-1555`.

20. National Bureau of Standards, *Precision Resistors and Their Measurement*,
    NBS Circular 470, 1958. Identifier: `NBS Circular 470`.

21. U.S. Army Corps of Engineers, *Hydraulic Design of Reservoir Outlet Works*,
    Engineer Manual, 1980. Identifier: `EM 1110-2-1602`.

22. Leybold, *Fundamentals of Leak Detection: Pressure Rise and Pressure Drop
    Tests*, undated manufacturer technical reference, accessed 2026. Identifier:
    `Leybold Fundamentals of Leak Detection`.
