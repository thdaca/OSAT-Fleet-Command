# Measurable physics roadmap — Snapshot 5 research supplement

OSAT Fleet Command 0.2.5; reviewed 2026-09-05. Research recommendations only.
This document does not change an executable relation, candidate status, maturity,
calibration, experiment claim, health threshold, station or maintenance authority.
It supplements, rather than replaces, the existing family dossiers and
`EVIDENCE_CATALOG.md`. Proposed equations below are engineering hypotheses, not
equations claimed to have been validated by the cited OEMs.

## 1. Executive findings

1. Keep **relation → exact-machine calibration → residual**. The useful next
   addition is a documented measurement episode, not a bigger physics framework.
   A valve transition, unloaded service sweep or identified motion segment can
   make a small model identifiable where anonymous telemetry cannot.
2. Wire bonding has the best new documented acquisition lead. Hesse lists
   configurable CSV logging, stored sensor curves and process-data export.
   This is an option-specific machine-log route, not proof that WB-04 has it or
   that raw curves are available through GEM. [Hesse software](https://www.hesse-mechatronics.com/software/)
3. Control mode and acquisition gain can reverse the interpretation of an
   ultrasonic channel. Hesse distinguishes voltage-controlled, current-controlled,
   resonance-tracked and fixed-frequency operation and discusses adaptive sensor
   amplification. Freeze those semantics before fitting. [Hesse 2024 whitepaper](https://www.hesse-mechatronics.com/wp-content/uploads/2024/01/Doc-VE-White_Paper_Sensorverstaerkung-20240111-final.pdf)
4. Wafer-mounter vacuum timing is a distinct, potentially accessible mechanism.
   DISCO documents acquisition/release sequencing and mechanical consequences
   of residual suction. It does not document an exported analog pressure trace.
   This does not rehabilitate the rejected generic die-attach vacuum equation.
   [DISCO DFM2800 bulletin, 2014](https://www.disco.co.jp/eg/support/condition/doc/TNL2014-0002e.pdf)
5. Thermal time constants and contact-datum/compliance checks merit controlled
   trials. Their effective parameters can change for several benign reasons;
   they are not uniquely heater, bearing, clamp or tool-wear diagnoses.
6. There is no newly verified public OSAT machine-health corpus in this review.
   A new RWTH molding archive is a concrete industrial-analog lead, but its byte
   download returned an access challenge. It is not an executable local dataset.
   [RWTH dataset, 2026](https://publications.rwth-aachen.de/record/1016199/)
7. Final-test evidence should join connector identity and verified service events
   to measurements. An Experior field presentation reports insertion tracking
   and recovery after pin replacement, but supplies no reusable raw dataset or
   causal isolation of every yield change. [TestConX 2024](https://www.testconx.org/premium/wp-content/uploads/2024/TestConX2024s5p3Khoo_2019.pdf)
8. The first funded experiment should still validate the existing WS-01 residual
   with real approved current/speed measurements and independent load/context
   controls. A stronger literature catalog cannot substitute for that experiment.

### Scope and evidence method

The starting point was the actual nine family implementations, dossiers and
current evidence catalog. Searches covered OEM documentation, separate patents
for all nine families, publisher supplements, university repositories, GitHub,
Zenodo and Mendeley leads. Two independent research lanes covered WB/DA and
WM/MO/TF; the main review covered WS/SG/MK/FT, data access and reconciliation.
This was a bounded source-led engineering review, not a systematic review or an
exhaustive proof that public data do not exist. Dates above are publication dates
where given; undated live OEM pages were inspected on the review date.

Evidence labels used here: **documented capability**, **measured study**,
**patent disclosure**, **engineering inference**, and **unverified access**.
No equipment was contacted, no author was messaged, no production intervention
was performed, and no new external dataset was bundled. Commercial-use notes
are diligence flags, not legal opinions or patent freedom-to-operate clearance.

## 2. Recommended physics-engine evolution

Retain Step01's existing `core/` and `families/` ownership. Do not activate new
math in this release. For a later, separately authorized experiment:

- Describe the physical episode with machine/axis/circuit identity, phase event,
  timebase, units, control mode, sensor gain/filtering and approved context.
  Prefer existing measurement/experiment contracts; add a field only after an
  acquired file demonstrates that it cannot be represented clearly.
- Freeze a healthy fit and its operating envelope. Evaluate later episodes
  without silently adapting away a developing change. A separate research fit
  may estimate parameter drift; it must not overwrite the accepted calibration.
- Add one transient or profile implementation only when an experiment supplies
  adequate observations. A phase-resolved median/MAD profile is often a better
  nuisance model than an elaborate physical equation.
- Preserve the asynchronous low-rate channel architecture. A triggered burst
  is an offline research artifact first; a later high-rate acquisition path
  must not become a synchronized mega-row or an FFT in the ordinary tick loop.
- Report an effective parameter change, repeatability and confounders. Do not
  convert it into a failure probability, remaining life, new health state or
  causal fault name.

Simple identification choices are sufficient. Affine fits need independent
operating-point variation; one speed or correlated excitation cannot identify
multiple coefficients. First-order transients need a resolved onset and tail.
Cycle profiles need repeatable phase boundaries and separate dwell timing.
ARX is deferred: feedback can correlate input and disturbance, and an anonymous
coefficient vector is not automatically physical. Offline fitting costs roughly
O(Np²) for p small; evaluation is O(p) per point or O(B) per fixed B-bin episode.
No meaningful edge performance claim is made before measurement.

## 3. Canonical-station research table

All new entries below remain **unimplemented research proposals**, not runtime
statuses. Existing WS is `RUNTIME_RESEARCH`; existing accepted candidates are
`RESEARCH_ONLY` with literature-level semantics, not physical validation. New
literature warrants a documented research proposal only; it does not warrant an
automatic maturity promotion. N labels identify this document, not new code IDs.

| Station | Strongest current direction (unchanged) | New question / equation | Signals and units | Source / realistic access | Confounders and information | Experiment / recommended maturity |
|---|---|---|---|---|---|---|
| WM-01 | Tape-tension stability | N02 valve-to-vacuum event delay; optional p(t) transient | Valve/threshold events, t s; p Pa absolute; arm state | [DISCO bulletin](https://www.disco.co.jp/eg/support/condition/doc/TNL2014-0002e.pdf): controller sequence documented; export unknown | Circuit, workpiece seal, volume, temperature; release/acquisition consistency, not leak rate | E02; access/semantics trial, research-only |
| WS-01 | I − (a n + b), A; electromechanical load consistency, never cutting force | N13 synchronous vibration order; N14 passive coast-down coefficient | Acceleration m/s², tach angle rad; speed rad/s, time s | [DISCO DAD3660](https://www.disco.co.jp/eg/products/dicer/dad3660.html): current monitoring; tach/high-rate export unverified | Blade, coolant, process load, bearing type, drive braking; mechanical change not unique fault | E07 plus WS validation in §12; research-only |
| DA-01 | Closed-loop force/Z/temperature consistency | N05 isolated cooling τ; N08 reference touchdown drift | T K/°C, t s, heater/cooler state; z µm | [Besi 9800 TC next](https://www.besi.com/products-technology/product/9800-tc-next/): bond traces and parameter provision; exact fields unknown | Thermal path, adhesive, collet, encoder expansion, active compensation | E03/E08; research-only |
| WB-04 | Defined-phase USG electrical-load consistency | N01 deformation drift; N03 unloaded resonance; N10 clamp response | z µm, phase, gain; f Hz, T K; verified Z Ω and I A | [Hesse PiQC](https://www.hesse-mechatronics.com/piqc/), [K&S patent](https://patents.google.com/patent/US12235302B2/en): log options versus service-only/unknown | Tool geometry, guide, wire/pad, mount, control mode; no universal impedance reconstruction | E01/E04/E09; research-only |
| MO-01 | Clamp/transfer-pressure/temperature/vacuum consistency | N04 closing contact/compliance; N06 pre-resin evacuation; N12 isolated thermal τ | Gap m, force N, contact state; cavity p Pa; T K, t s | [Fico line](https://www.besi.com/products-technology/product-details/product/fico-molding-line/): relevant controls; [Fico patent](https://patents.google.com/patent/US6165405A/en): force/gap embodiment; export unknown | Mold expansion, resin/cure, control law, separate vacuum circuits | E05/E06/E03; research-only |
| MK-01 | Commanded versus measured optical output | R01 two-plane transmission/monitor disagreement; refinement, not claimed novel | Simultaneous P_internal/P_external W, pulse state, temperature | [KEYENCE](https://www.keyence.co.in/products/marker/laser-marker/industries/ai-data-center.jsp?ad_local=cbgt): internal monitoring; independent meter required | Monitor plane/gain, optics, pulse aggregation, beam alignment | E10; retain current research-only candidate |
| TF-01 | Stroke-aligned servo/force profile | N11 unloaded following-error residual, excluding material contact | x_command/x_actual m, phase, velocity m/s, tuning ID | [Besi trim/form](https://www.besi.com/products-technology/product-details/productgroup/trim-form/): host option, not proof of trajectory export | Cam geometry, backlash, interpolation, temperature, tuning and clock skew | E11; research-only |
| SG-01 | SG-only current/speed residual proposal | N13 order response on actual SG spindle, independently calibrated | Acceleration m/s², tach angle rad, coolant/tool phase | [DISCO package-singulation specification](https://www.disco.co.jp/eg/products/dicer/dad3660.html); high-rate access unknown | Package stack, blade mounting, dual spindles and water accumulation | E07 on SG separately; research-only |
| FT-01 | Handler motion signatures; separate contact-resistance metrology | R02 offset-cancelled, force-conditioned contact repeatability; refinement | Signed V V, I A, F N, socket T K, contact/site IDs | [Cohu Kelvin contacts](https://www.cohu.com/interface-solutions/); four-wire path/force generally needs qualified fixture | DUT/test path, plating, force distribution, thermoelectric offset, self-heating | E12; retain research-only; no runtime equation activation |

### Patent and telemetry-access ledger

These are technical disclosures, not permission to copy patented procedures.
No SVID number is invented; a host/GEM option does not establish which channels
are exported or their bandwidth.

- **WM:** [EP3705862B1, Infineon](https://patents.google.com/patent/EP3705862B1/en)
  describes optical approaches to tape-tension monitoring. Already represented;
  not new PHM evidence. DFM2800 sequence events have stronger direct OEM grounding
  for N02, but analog export remains unknown.
- **WS:** [US6168500B1](https://patents.google.com/patent/US6168500B1/en)
  describes dicing-saw speed feedback and sampled spindle current. A disclosed
  sampling range is not a promised bandwidth for an installed DISCO model.
  DAD3660's published monitoring categories do not supply a customer tag map.
- **DA:** [ASMPT US20080017293A1](https://patents.google.com/patent/US20080017293A1/en)
  describes contact sensing and relative encoder movement; thermal expansion
  and tip wear affect touchdown. [ETEL EP4657511A1, 2025](https://data.epo.org/publication-server/rest/v1.2/publication-dates/2025-12-03/patents/EP4657511NWA1/document.pdf)
  identifies thermal encoder/head-offset effects. Internal sensing is not proof
  of customer-visible following error. Do not add dual encoders by default.
- **WB:** [K&S US9016107B2, 2015](https://patents.google.com/patent/US9016107B2/en)
  describes controlled-voltage resonance calibration; [US12235302B2, 2025](https://patents.google.com/patent/US12235302B2/en)
  considers impedance across current operating points after tool changes.
  Both are controlled tests, not justification for dividing unspecified channels.
  Hesse's curve export is an independent commercial route; do not infer K&S tags
  or procedures from Hesse documentation.
- **MO:** [Fico US6165405A](https://patents.google.com/patent/US6165405A/en)
  places force, mold-gap and contact-state observations in a defined closing
  sequence. Customer export is unverified. [TOWA US10170346B2](https://patents.google.com/patent/US10170346B2/zh)
  was checked as a competing lead: a pressure-sensor reference concerns the
  encapsulated device, not evidence of an equipment telemetry channel.
- **MK:** [US9116131B2](https://patents.google.com/patent/US9116131)
  discusses separate illumination/scattered/reflected observations of optical
  contamination. It supports optical-path confounding, not built-in availability
  on MK-01. Internal optical monitors, pulse energies and service outputs remain
  architecture/model-specific; external reference metrology is still required.
- **TF:** [Apic Yamada EP0881046A2](https://patents.google.com/patent/EP0881046A2/en)
  describes lead-frame press feeding, cams and motion phases. It explains why
  motor load cannot be equated directly with punch force. Following-error tags
  are **unknown**, not asserted likely through GEM.
- **SG:** [US20200176315A1, DISCO](https://patents.google.com/patent/US20200176315A1/en)
  concerns package-substrate division, not a telemetry-export specification.
  [TW200539336A, saw singulation](https://patents.google.com/patent/TW200539336A/en)
  is additional mechanism context. Neither supplies a public SG health stream.
- **FT:** [US10955438B2](https://patents.google.com/patent/US10955438B2/en)
  describes mechanical/contact degradation and contamination; [WO2025127372A1](https://patents.google.com/patent/WO2025127372A1/en)
  highlights spatial force-distribution effects. A socket structure is not a
  promise of resistance, force or per-pin telemetry from the handler.

For a Tier-2/3 OSAT, first request a **field list and small approved export**, not
controller internals. Allowed categories are reviewed current/speed/temperature,
physical phase and sensor-quality metadata, pseudonymous tool/site identity and
adjudicated service events. Bond coordinates, maps, PPIDs, recipes, process
windows and unapproved constants remain outside ingestion. Only approved opaque
context strata may be used to block experiments. If that cannot control a
confounder, abstain instead of collecting restricted process IP.

## 4. Novel candidate ranking

Ordinal triage, not evidence points or predicted ROI. Each vector uses 0/1/2
(absent-or-poor / conditional / strong) in this order: physical defensibility,
machine relevance, signal availability, identifiability, falsifiability,
diagnostic usefulness, simplicity, source quality, **acquired useful data**.
Sum /18 is only a transparent sorting aid; ties favor lower acquisition burden.
Every last component is zero: no newly acquired target-machine dataset.

| Rank / proposal | Vector; total | Classification | What is genuinely different from the existing catalog |
|---|---|---|---|
| 1 N01 WB deformation-profile drift | 2,2,2,1,2,1,2,2,0; 14 | NOVEL AND HIGH PRIORITY, conditional on suitable Hesse heavy-wire access | Mechanical deformation and tool-life chronology, not USG load |
| 2 N02 WM valve response | 2,2,1,1,2,1,2,2,0; 13 | NOVEL AND HIGH PRIORITY for access trial | Event-conditioned response time, not tape tension |
| 3 N03 WB unloaded resonance drift | 2,2,1,1,2,1,2,2,0; 13 | NOVEL BUT NEEDS SIGNAL ACCESS | Isolated mode parameter outside the bond, not in-bond electrical load |
| 4 N04 MO force-gap contact/compliance | 2,2,0,1,2,1,2,2,0; 12 | NOVEL BUT NEEDS SIGNAL ACCESS | Independent gap/contact observation, not pressure/force correlation |
| 5 N05 DA cooling time constant | 2,2,0,1,2,1,2,2,0; 12 | NOVEL BUT NEEDS SIGNAL ACCESS | Controlled passive transient, not static temperature/force consistency |
| 6 N06 MO pre-resin evacuation | 2,2,0,1,2,1,2,2,0; 12 | NOVEL BUT NEEDS SIGNAL ACCESS | Fixed-volume phase; same new transient idea as N02, not separate novelty credit |
| 7 N08 DA reference touchdown datum | 2,2,0,1,2,1,2,2,0; 12 | NOVEL BUT NEEDS SIGNAL ACCESS | Rigid reference geometry across thermal blocks, not production compliance |
| 8 N10 WB clamp-response curvature | 1,2,0,1,2,1,2,2,0; 11 | NOVEL BUT NEEDS SIGNAL ACCESS and IP review | Multi-level controlled coupling test, not a new name for impedance |
| 9 N11 TF unloaded following error | 2,2,0,1,2,1,2,1,0; 11 | NOVEL BUT NEEDS SIGNAL ACCESS | Command/encoder disagreement outside tooling contact |
| 10 N12 MO thermal recovery | 2,2,0,1,2,1,2,1,0; 11 | NOVEL BUT NEEDS SIGNAL ACCESS | Same new transient idea as N05; not separate novelty credit |
| 11 N13 WS/SG synchronous order response | 2,2,0,1,2,1,1,1,0; 10 | NOVEL BUT NEEDS SIGNAL ACCESS | Tach-referenced high-rate burst, unavailable from scalar RMS |
| 12 N14 WS passive coast-down ratio | 1,2,0,1,2,1,2,1,0; 10 | INTERESTING BUT LOW VALUE until an OEM routine exists | Drive-off dynamics; separate from powered current/speed calibration |

This is **ten distinct new measurement/identification ideas**, with two extra
station applications of shared transient ideas. R01 optical two-plane comparison
and R02 contact metrology below are useful **refinements of existing candidates**,
not counted as novelty. Neither are generic cycle energy, parameter tracking by
itself, SG reapplication of WS, or a renamed TF stroke profile.

## 5. Exact equations and validation conditions

These are proposed offline experiment summaries. No equation is evaluated from
arbitrary text. Canonical telemetry unit strings remain unchanged; convert only
an explicitly approved offline copy with Pint. Temperature differences are K;
absolute pressure must not be confused with signed gauge pressure. Proposed
sample/repetition counts are acquisition starting points, not validated power
calculations or acceptance thresholds.

### N01: deformation profile and slow parameter change

For bond j, define contact-referenced deformation d_j(φ)=z_j(φ)−z_j(contact),
with z in µm and φ∈[0,1] a documented monotonic bond-phase coordinate. For each
fixed phase bin, m(φ)=median_healthy d_j(φ), s(φ)=median_healthy |d_j(φ)−m(φ)|.
Report signed terminal drift Δd_j=d_j(1)−m(1) in µm and
R_j=median_φ {|d_j(φ)−m(φ)|/max[s(φ),s_resolution]} (dimensionless).
Use linear interpolation only inside a continuous observed phase; never bridge
missing segments or align distinct physical phases. Keep duration separately.

Fit only healthy reference coupons from the same exact machine/tool class.
Tool wear linkage was measured for a specific heavy-copper wedge process;
fine-wire capillary transfer is unverified. [Hesse IMAPS study, 2015](https://www.hesse-mechatronics.com/wp-content/uploads/2019/10/broekelmann_et._al._-_copper_wire_bonding_imaps_2015_hesse_mechatronics.pdf)
Do not label the generic summary above as Hesse's proprietary quality algorithm.

### N02/N06: valve response, not a generic leak equation

Minimum form: Δt=t_threshold−t_valve, seconds. Record the actual threshold
identity; a changed threshold invalidates comparison. With a stable-volume,
uninterrupted state, propose
p(t)=p∞+(p0−p∞)exp[−(t−t0)/τ], p in Pa absolute, t and τ in s.
All terms are Pa and the exponent is dimensionless. t0 comes from a logged
event; fit p∞ and positive τ by bounded least squares, not by freely exchanging
delay and τ. Require a resolved tail and inspect residual shape.

For an isothermal effective volume V (m³), constant effective pumping speed S
(m³/s) and gas throughput q (Pa·m³/s), V dp/dt=q−Sp gives τ=V/S and p∞=q/S.
This derivation explains **why τ does not identify leakage q** without V, S and
boundary conditions. WM release may be nonlinear choked flow; use the event
interval only if the exponential is falsified. MO filling changes volume and
gas/thermal conditions, so this model is limited to an isolated pre-resin phase.

### N03: unloaded resonance drift

Use an OEM-approved low-amplitude sweep and identify the same isolated mode by
its documented current maximum or phase criterion. Fit f̂_r(T)=a+b(T−T_ref)
on healthy sweeps: f_r,a in Hz, b in Hz/K, T in K. Report r_f=f_r−f̂_r in Hz,
plus the temperature-block repeatability. Two thermal levels are algebraically
enough for a line; at least three and repeated sweeps are needed to challenge it.
Mode switching, contact loading or unlogged remounting require abstention.
No equivalent-circuit parameters are inferred from one current/frequency pair.
[K&S calibration patent](https://patents.google.com/patent/US9016107B2/en)

### N04: closing contact and effective compliance

In a quasi-static monotonic contact interval, x=x_c+C_eff(F−F0).
Gap/displacement x,x_c are m; F,F0 are N; C_eff is m/N. Define the displacement
sign and reference force F0 before fitting; otherwise x_c is an arbitrary
intercept, not physical first contact. Fit a line at several independent loads,
inspect loading/unloading separately and report C_eff and contact-event position.
Independently measured force and gap are required; two controller quantities
calculated from one another do not identify stiffness. k_eff=1/C_eff is N/m
only when nonzero compliance is resolved above uncertainty.

### N05/N12: passive thermal response

Under a fixed thermal boundary, C dT/dt=P−(T−Ta)/Rθ, with C in J/K,
P in W, Rθ in K/W and t in s. Both right-hand terms are W. For passive cooling
P=0 and approximately constant Ta:
T(t)=Ta+(T0−Ta)exp(−t/τ), τ=Rθ C in s.
Fit positive τ by bounded least squares, using a measured stable Ta where
possible. If Ta is fitted, require enough tail to separate it from τ. A first-order
fit cannot separately identify Rθ and C. Steady Rθ=(T−Ta)/P requires measured
watts at the defined boundary; heater duty percent is not watts. Active PID,
multiple zones, changing contact/coolant or a second dominant mode can invalidate
the equation. Prefer abstention or the existing descriptive profile over adding
a high-order thermal network merely to improve fit.

### N08: contact-datum drift on a reference artifact

z_contact=a+Σ_i b_i(T_i−T_i,ref)+r_z; z,a,r_z in µm, b_i in µm/K.
Start with one physically relevant temperature; do not fit correlated zone
temperatures as if independently identifiable. Use independently checked
reference heights, fixed approach direction/speed and a fixed tool. Fit healthy
blocks and validate on another day. This measures geometric repeatability,
not die thickness, adhesive compliance or uniquely tool wear.

### N10: controlled clamp-response curvature

Only with verified impedance and a fixed resonance/control condition, let
u=I/I_ref and Z(I)=a+b u+c u², with I,I_ref in A and Z,a,b,c in Ω.
Fit at least five distinct allowed current levels, with repeats, and compare
healthy pointwise behavior and c across thermal/remount blocks. The polynomial
is a local empirical summary, not a constitutive law or clamp-force estimator.
Prefer an exported existing OEM service-test result to reproducing a patented
diagnostic procedure. [K&S connection-check disclosure](https://patents.google.com/patent/US12235302B2/en)

### N11: unloaded following error

e(s)=x_command(s)−x_actual(s), E_x=sqrt[∫₀¹ e(s)² ds], with x,e,E_x in m
and normalized segment coordinate s dimensionless. Keep signed peak error and
segment time in s as separate observables. For a dwell, use elapsed time, not a
position normalization with zero range. No current-to-force conversion is used.
Identical commanded trajectory, interpolation, tuning and common timebase are
essential. A timestamp shift δt alone produces apparent error near v δt.

### N13: order response; research burst only

For acceleration samples a(θ_k) in m/s² uniformly resampled over an integer
number of revolutions, A_m=(2/N)|Σ_k a(θ_k)exp(−i m θ_k)|, in m/s²,
for positive order m below the resampled Nyquist limit. State window/coherent
gain if a window is used. Compare A_1,A_2 against exact-machine speed/context
bins; do not divide by a near-zero reference amplitude. Order m occurs at
f_m=m n/60 Hz for speed n in RPM. At 60,000 RPM, order 4 is 4 kHz: sampling must
exceed 8 kHz and include a real anti-alias transition band; 20 ksample/s is a
proposed starting acquisition rate, not an existing OEM capability.
[NI order-analysis requirements](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA03q000000YNVFCA4&l=en-US)

A tach/encoder plus bandwidth-qualified acceleration is required. Scalar RMS
and occasional speed readings cannot reconstruct orders. Many dicing spindles
use non-rolling-bearing architectures: bearing characteristic-frequency formulas
require actual bearing identity and geometry. Never invent those constants.

### N14: passive coast-down, conditional and low priority

If an existing safe OEM routine genuinely disables drive torque and braking,
J dω/dt=−bω−τ_c for one direction over a bounded speed range. Fit
dω/dt=−αω−β, with ω rad/s, α=b/J in s⁻¹ and β=τ_c/J in rad/s².
Prefer the integrated solution ω(t)=(ω0+β/α)exp(−αt)−β/α when α>0,
fitting α,β≥0 rather than differentiating noisy speed. α/β are effective ratios;
J, bearing friction and coolant drag are not separately identified. Braking,
air-bearing supply or coolant changes invalidate inference. Never command a
coast-down or defeat interlocks from Fleet Command. Run-up/down literature on a
laboratory grinding rotor is only an analog, not validation of this proposed
fit on a dicer. [Laboratory spindle study](https://www.sciencedirect.com/science/article/pii/S0924013606011228)

### R01/R02: useful refinements, not novelty credits

R01: q=P_external/P_internal is dimensionless only for commensurate calibrated
optical power in W, matched time/pulse aggregation and defined planes. Compare
q with a healthy same-architecture reference. A path loss versus internal-monitor
disagreement can narrow an investigation, but neither isolates source efficiency.
Electrical efficiency P_opt/P_elec requires measured real electrical power,
including the declared boundary. Fiber, DPSS, direct diode, UV and CO₂ systems
must not share coefficients or an assumed diode-current law.

R02: with signed Kelvin voltages V+ and V− at equal currents +I and −I,
R_c=(V+−V−)/(2I), Ω; a stable thermoelectric offset cancels. Fit a local healthy
R̂_c(F,T) only with independently measured force N and temperature K. Use an
instrumented dummy/reference path so DUT resistance is not confused with socket
resistance. Current reversal must be safe for that path and fast relative to
offset change. [Keithley measurement guidance](https://www.tek.com/tw/documents/whitepaper/accurate-low-resistance-measurements-start-identifying-sources-error)

### Energy, ratios and uncertainty

Dimensional ledger: ∫P dt is J when P is measured W; ∫F dx is N·m=J;
∫τ ω dt is J with torque N·m; ∫Δp Q dt is hydraulic work J for pressure Pa
and volumetric flow m³/s at a declared boundary. ∫I²dt is **A²·s**, not energy;
it becomes resistive heat only with appropriate resistance and electrical
semantics. Percent-load·s, controller counts·ms and ∫position-error²dt (m²·s)
must retain their units and be called effort/response summaries. Work per stroke
is already a refinement of the TF profile, not a new physics family. Integrate
only complete, timestamp-aligned phases with a declared missing-data policy.

Use dimensionless residuals only when numerator and denominator are the same
quantity and the denominator is resolved above uncertainty. A/RPM is not a
dimensionless load, temperature-rise/power has K/W, and force/displacement has
N/m. Buckingham-π does not recover missing geometry or controller semantics.

Keep u_r=sqrt(J_r Σ J_rᵀ). First-order propagation is appropriate for smooth,
locally linear measurement functions with a defensible covariance budget;
include shared calibration and fitted-parameter covariance. It is not a
confidence interval for failure probability. [NIST TN1297 Appendix A](https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-appendix-law-propagation-uncertainty)
For peak selection, medians, low denominators, fit-boundary solutions and
temperature/timebase systematics, prefer independent repeated-calibration
distributions and explicit sensitivity tests. If bootstrap intervals are later
used, resample independent runs/tool lives or day blocks, not correlated samples;
predeclare the estimator, block unit, seed and interval method. No new confidence
interval is invented for the two-positive D1 result.

## 6. Reusable primitive assessment

No framework or registry is justified now. Reuse only small numerical functions
after at least two acquired relations demonstrate equal semantics:

- **First-order response fit:** N02/N06 share constant-volume pressure semantics
  only in qualified phases. N05/N12 share passive thermal assumptions. They may
  reuse a bounded exponential fitter; pressure/thermal validity, units, episodes,
  parameters and calibrations remain family-owned. WM release may fail this model.
- **Fixed-phase profile summary:** N01 and N11 can reuse bin/interpolation/MAD
  mechanics only after agreeing on monotonic phase, gaps and clock policy. Their
  physical channels and units are not interchangeable. Existing TF load profiles
  remain distinct from unloaded position following error.
- **Existing affine/uncertainty routines:** retain where their actual inputs and
  fit assumptions match. Never share WS/SG fitted parameters or exact-machine
  baselines just because a helper is shared.
- **Do not generalize** optical ratios, acoustic impedance, motor current and
  contact resistance into one electrical-consistency relation. The feedback,
  bandwidth, phase and physical boundaries differ. No generic actuator twin,
  free-form equation interpreter, automatic primitive selection or plugin layer.

## 7. Data discoveries and access outcomes

No entry below is promoted to `REAL_OSAT`, fed into Step05, or given operational
ticket authority. “Requestable” means a plausible owner/contact exists, not
that permission has been granted. “Public-listed” is weaker than successfully
acquired, hashed and schema-verified bytes. Unknown fields are explicitly unknown.

### Public-listed industrial analog: RWTH injection molding (new)

[10.18154/RWTH-2025-06809](https://publications.rwth-aachen.de/record/1016199/),
posted 2026; `ExperimentalData.zip` listed as 1,007.55 KB. Recorded Arburg
Allrounder 520 A 1500-800 trials include cavity/antechamber pressure, controller
output, screw velocity, volume and part-mass/reference records. Landing-page
rights: CC BY 4.0. The attempted byte request returned HTML challenge content;
no raw archive/hash, per-file license, units, sampling, timestamps or run schema
was verified. Machine model is named, serial identity unknown; process-control
trials are described, maintenance/failure truth is not. Not currently executable
through Step01/03/07/09. Potential commercial reuse requires attribution and
checking actual archive rights; this is plastics injection molding, not OSAT.

### Public-listed thermal design analog: MicroAnalytix (new)

[10.17632/gwnt75p22n.1](https://data.mendeley.com/datasets/gwnt75p22n/1),
2024, University of Twente; CC BY 4.0 landing-page license. Describes analytical
microchannel thermal/hydrodynamic design comparisons, not laser-source aging.
The fetched page exposed no file manifest or usable byte link: size, file types,
raw versus simulated composition, signals/units, timestamps and run boundaries
unverified. No installed OSAT machine identity or maintenance labels. Exclude
from executable PHM claims; low-priority contact/manifest inquiry only. It cannot
validate Step01/03 or supply a Step07 baseline; no Step09 use. Commercial reuse
is conditional on actual files matching the stated license and attribution.

### Requestable OEM traces: Hesse WB (new acquisition route)

[Hesse software](https://www.hesse-mechatronics.com/software/) and
[PiQC](https://www.hesse-mechatronics.com/piqc/) document stored curves and
process records. Possible observations include deformation, electrical current,
frequency change and derived quality quantities. Actual schema, units, sampling,
timestamp/event keys, machine IDs, file size and raw/derived distinctions require
an approved sample export. Maintenance truth must come from independent tool
records/inspection. No public data license; ownership and commercial use need
written agreement. An approved phase subset could support N01/N03 offline;
existing Step01/03 do not execute them and Step09 remains unchanged.

### Paper-only / requestable: heavy-copper tool-wear study (new lead)

[Brökelmann et al., IMAPS 2015](https://www.hesse-mechatronics.com/wp-content/uploads/2019/10/broekelmann_et._al._-_copper_wire_bonding_imaps_2015_hesse_mechatronics.pdf)
reports deformation and inspected wear in a particular heavy-wire setup, with
tool/guide dependence. Published figures are not raw time series. Corpus size,
unit schema, timestamps, machine serials and run files unknown; no public raw
license. Ask for anonymized bond curves with inspected tool-life blocks and
rights. It is process/tool evidence, not fleet failures or WB-04 validation.
No existing Step01/03/07/09 execution without a separately reviewed mapping.

### Paper-only: 600 wire-bond laboratory trials (new)

[Buchner et al., 2025, DOI 10.1007/s10845-025-02615-3](https://doi.org/10.1007/s10845-025-02615-3)
uses a Delvotec M17S with 380 µm copper wire, 200 settings and three trials each,
with shear measurements. The energy objective is controller-unit·time, not
validated joules. Data/code availability is “Not applicable”; no supplementary
raw file was located. Byte size, full unit schema, timestamps and serial IDs
unknown; experimental trial boundaries described, no maintenance/aging labels.
Semiconductor-interconnect laboratory evidence, not confirmed OSAT production.
Article openness does not grant a nonexistent data corpus. Request rights and
physical semantics before any later offline use; no present pipeline mapping.

### Paper-only / requestable: FHNW–Hitachi transfer molding (new)

[Kocher et al., COMSOL Conference 2025](https://www.comsol.com/paper/download/1612771/FINAL_TransferMolding_COMSOL_Amsterdam-2025.pdf)
compares semiconductor-module short-shot experiments with simulation. Resin
flow/cure, packing and foaming complicate interpretation. Public figures only;
raw file size, time-series units, machine serials, timestamps and full shot
manifest unknown. Shot/process truth is not equipment maintenance truth.
No raw commercial-use license found. Request pressure/temperature traces and
shot definitions under agreement; no current Step01/03/07/09 execution. Do not
import the multiphysics software merely because it appears in this study.

### Paper-only / requestable: Experior socket field records (new)

[TestConX 2024 socket-pin tracker](https://www.testconx.org/premium/wp-content/uploads/2024/TestConX2024s5p3Khoo_2019.pdf)
shows field insertion/yield histories and a replacement-associated recovery.
No public raw attachment, byte size, socket serial schema, timestamps, resistance
units or independent fault-adjudication record. Lot/site histories are shown,
not continuous sensor runs. Potential OSAT-relevant field evidence; origin and
rights of any received records must be established separately. Request approved
socket IDs, insertions, service boundaries and metrology, not DUT process IP.
No direct current Step01/03/07/09 fit; do not reproduce the presentation's
automation or intervention claims in Fleet Command.

### Existing leads rechecked, not counted as discoveries

- [CHDL / DIFFUMA, arXiv 2507.06738](https://arxiv.org/html/2507.06738v1)
  calls its dicing-image dataset public, but this review did not locate a working
  author dataset link or byte manifest. The HTML's GitHub links were rendering
  support, not the dataset. Size/license and maintenance truth remain unverified.
  Images are not current/speed telemetry; no Step01/03 mapping is implied.
- ST-AWFD and TUHH remain the already-known sources, not new discoveries.
  See POST04's exact pinned rights, byte identity and methodology inventory.
  ST normalized features support an external scoring comparison, not physical
  unit calibration or frozen Step09 threshold transfer. TUHH surface maps are
  target-process descriptive evidence, not failure-lifecycle telemetry.
- The existing PTI, Amkor, ASE, UTAC and final-test-paper leads remain in
  `EVIDENCE_CATALOG.md`; this search found no newly verified downloadable
  maintenance-labeled corpus that changes their access classification.
- Separate queries for wafer mounting, trim/form, dicing vibration, socket
  resistance and laser degradation in dataset repositories did not yield a
  new verified target-machine corpus. This is a search outcome, not an assertion
  that none exists. Do not replace missing evidence with simulated bytes.

Next data action: obtain one rights-approved, metadata-complete machine export.
Before decoding, confirm source authorization; then hash exact bytes, inspect
units/timebase/events, keep raw files ignored and out of releases, and separately
review whether any evidence-origin claim is justified. A DOI or OEM name alone
does not satisfy the existing PRE03 V2 verification boundary.

## 8. Controlled experiments

All are **proposals**, not completed experiments or changes to `ExperimentPlan`.
OEM/site staff own safe settings, access and ground truth. Use dummy/reference
material and approved engineering routines; no bypassed interlock, deliberate
production damage, autonomous adjustment or invented safe operating range.
Rates below are requested acquisition targets, contingent on sensor bandwidth;
never upsample a slow export and call it high-rate evidence. Each trial includes
restoration/retest, sensor/clock negative controls and later-day holdout.

### E01 — high priority: WB deformation/tool-life trial (N01)

One appropriately equipped heavy-wire bonder first; no assumed transfer to
fine-wire WB-04. Capture µm deformation, phase/time, tool identity, control/gain
and approved context. Request at least 20 genuine samples in the shortest phase:
f_s ≥20/t_phase (e.g. 2 kHz for 10 ms); actual OEM bandwidth must be verified.
Use three independently inspected tool conditions/lives, 30 reference-coupon
bonds per condition and two day blocks. Randomize coupon/order within safe
blocks; hold wire/pad/force program fixed and block guide adjustment and tool
geometry. Plan roughly half a day of acquisition plus metrology, not a full
tool-life study. Ground truth: blinded tip microscopy/profilometry and shear.
Support: repeatable deformation change with inspected wear after context blocks.
Weaken/falsify: guide/material changes explain equal or larger change and wear
adds no repeatability. Abstain on changed geometry, gain/clipping, missing phase
or unknown Z datum. Wear link is measured in the cited setup; transfer is only
plausible until this test succeeds.

### E02 — high priority access trial: WM valve timing (N02)

Dummy wafer, fixed identified arm/table circuit and motion phase. Record valve
events/thresholds, pressure Pa absolute, time s and arm state; target 100–500 Hz
if supported. Ten repetitions per permitted service condition in two day/thermal
blocks; randomize approved restriction conditions within blocks, restore and
repeat. Allow 1–2 hours plus reference setup. Independent pressure reference and
OEM service inspection supply truth. Support: repeatable response change under
the independently verified perturbation. Falsify: alignment/gauge correction
removes it or normal sealing variation dominates. Abstain on valve overlap,
moving volume, unidentified gauge reference, absent trigger or insufficient
samples. Valve/restriction response is strongly plausible; specific leak cause
is unsupported. No historic bulletin setting becomes a Fleet Command threshold.

### E03 — DA/MO passive thermal trials (N05/N12)

Run each machine separately. Record T and ambient K, time s, heater/cooler state,
contact/tool state; 1–5 Hz initially, then require ≥20 samples per fitted τ and
an observed tail near ≥3τ where safe. Three permitted starting temperatures,
ten repeats per DA block over two sessions; for slow MO cycles begin with three
repeated complete cycles on each of two days and report the small sample count.
Block tool/cooling configuration; randomize only thermally feasible order.
Budget one engineering day or longer if the cooldown tail demands it. Independent
thermocouple and documented cooling restoration, not invented fault labels.
Support: identifiable τ with held-out repeatability and reference agreement.
Falsify: benign boundary/control changes or multiple modes dominate the fit.
Abstain during unknown PID action, contact/heat-load changes or sensor drift.
Thermal-path change is plausible; heater failure and separate Rθ/C are not proven.

### E04/E09 — WB service resonance/clamp trials (N03/N10)

Use existing OEM-authorized test routines only. Three temperature blocks, three
approved remounts, at least ten repeat sweeps each, repeated on another day.
Record Hz/K/mode/gain and, for N10, at least five allowed A levels with verified
Ω. Sweep dwell must allow settling; store every native sweep point, not a
fabricated generic sample rate. Plan a half day plus inspection. Independent
frequency reference/vibrometer for N03; OEM gripping/installation inspection
for N10. Randomize sweep order, block tool identity and temperature. Support:
repeatability and response to independently assessed conditions. Falsify: normal
remounting/heating explains the entire effect. Abstain at mode switching,
unknown impedance semantics or clipping. Mount/transducer change is plausible;
specific wear diagnosis remains weak. N10 requires patent/IP review first.

### E05/E06 — MO compliance and pre-resin vacuum (N04/N06)

Separate qualified empty-tool phases, not live resin filling. For compliance,
record independent N/m force/gap/contact at 100–1000 Hz; ten repeats at three
approved loads in two hot-tool blocks. For vacuum, record the actual cavity
circuit, valve state and absolute Pa at 100–500 Hz; ten repeats per approved
service condition in two thermal blocks. Plan half a day to one day including
warm-up. Block mold/seal/temperature; randomize permitted test ordering.
Ground truth: load/gap reference, OEM vacuum/hold test and approved restoration.
Falsify if derived controller channels are circular, reference measurements
remain unchanged, or normal expansion/pump variation dominates. Abstain without
quasi-static contact or fixed sealed volume. Seating/compliance/restriction
changes are plausible; contamination, leakage and clamp failure are not unique.

### E07 — WS/SG order trial; optional coast-down screen (N13/N14)

Independent trials and calibrations per spindle/machine. Acquire acceleration
m/s² at an anti-aliased rate selected from maximum speed/order (20 ksample/s is
only an initial example), synchronized tach and coolant/tool/phase metadata.
Three approved speed plateaus, ten 2-second bursts each across two thermal blocks;
repeat after a normal inspected service action. Randomize safe plateau order.
Allow several hours; use OEM balance/runout inspection as independent truth.
Falsify when mounting/coolant/context effects dominate or no repeatable order
change accompanies an independently verified condition. Abstain without tach,
bandwidth, known spindle architecture or sensor mounting. Imbalance-related
synchronous motion is physically established; bearing-wear diagnosis is not.
N14 is only a feasibility screen on an existing safe routine: ten native-rate
speed traces, documented drive/brake state and restored boundary. No such routine
means **defer**, not modify machine control.

### E08/E10/E11/E12 — remaining focused trials

- **DA datum:** three temperature blocks ×20 reference contacts at two checked
  heights; fixed approach, 1 kHz/native synchronized contact/encoder capture or
  validated event latching; half day plus later-day repeat. Block collet, randomize
  reference heights. Independent artifact metrology. Falsify if reference repeats
  are unstable or hidden compensation explains change; abstain on unknown datum.
- **MK optical:** three approved output/pulse conditions ×10 readings in two
  thermal blocks, matched internal/external power integration windows; ≥10 Hz
  logging only if meters genuinely resolve it. Approved external attenuator
  in a guarded test setup, randomize its order; half day. Independent calibrated
  optical meter. Falsify if plane alignment/monitor drift dominates; abstain on
  unmatched pulse regime. Source-versus-path separation is plausible, not diagnosis.
- **TF following error:** 20 dry strokes at each of two approved speeds and two
  warm/cold blocks, initially 1 kHz/native command/encoder logging; 1–2 hours plus
  warm-up. Block tuning, randomize permitted stroke sequences. Independent
  position/service assessment. Falsify if clock skew or changed interpolation
  explains residual; abstain with missing command or unidentified cam mapping.
- **FT contact:** instrumented dummy, three independently verified force levels
  ×20 insertions ×two thermal blocks, synchronized event-latched Kelvin pairs
  after settling, not a universal high-rate demand. Randomize safe force order;
  block site/pin set and test temperature. Half day plus metrology. Independently
  inspect pins and compare before/after an approved cleaning/replacement.
  Falsify if reference path or force distribution explains apparent resistance
  drift; abstain without isolated path, stable offset or known current. Contact
  contamination can increase resistance; this experiment must separate it from
  product and force effects before claiming an equipment cause.

## 9. Rejected ideas

1. **Generic DA vacuum leak law:** still rejected. A new WM sequence source says
   nothing about DA sensor access, closed volume or leakage identifiability.
2. **Universal USG V/I or full equivalent circuit from low-rate channels:**
   unidentifiable without phase/control/acquisition semantics. More equations
   would conceal, not resolve, the missing information.
3. **Current equals cutting/punch force:** drive losses, acceleration, geometry,
   coolant and controller feedback prevent that inference. Unknown torque
   constants cannot be supplied from another machine's calibration.
4. **Current²-time or controller-count-time called joules:** dimensional error.
   Retain a clearly named effort summary only when independently useful.
5. **Generic FFT/envelope library in Step03:** slow scalar telemetry cannot
   reconstruct the required waveform. Dedicated qualified bursts must come first.
6. **Universal laser efficiency model:** source architectures and optical planes
   differ; pump current, emitted power and delivered power are not interchangeable.
7. **End-to-end neural diagnosis or generic ARX to fill semantic gaps:** omitted
   context and feedback bias remain, regardless of predictive fit.
8. **Automatically self-updating calibration/thresholds:** can erase degradation
   and changes the frozen evidence methodology. Parameter tracking stays separate.
9. **Patents/marketing as plant validation or implementation permission:** neither
   supplies fleet bytes, prospective outcomes or freedom to operate.
10. **Recipe collection to improve a residual:** conflicts with the approved
    equipment-health boundary. Use approved context or abstain.
11. **DUT yield drift as socket/handler diagnosis:** product/process changes and
    site configuration can explain it. Join independent service/metrology first.
12. **Giant shared physical-primitives framework:** fewer than two acquired,
    semantically equivalent consumers is insufficient justification.

## 10. Step01 implementation recommendation for a later prompt

Nothing in this section is implemented by Snapshot 5.

1. **Leave unchanged:** every existing relation/candidate ID, equation, status,
   maturity, reference claim, uncertainty calculation and experiment result;
   particularly WS current/speed, separately owned SG, WB defined-phase load,
   rejected DA vacuum, and all downstream stages.
2. **First collect, do not code:** approved WS current/speed semantics and a small
   Hesse/WM field-list export. Record source owner, rights, exact machine, clock,
   raw/derived meaning, unit, phase, gain and independent reference measurements.
3. **Candidates to add later as research-only metadata:** N01, N02, N03, N04,
   N05 and N08, only after source review by the project lead. Keep N06/N12 as
   separately owned applications, not evidence duplication. N10 needs access/IP
   clearance; N11/N13 need actual signals. Leave N14 deferred.
4. **Candidates to refine later:** existing optical-output and contact-resistance
   dossiers with the R01/R02 metrology protocol; existing TF profile with truthful
   work/effort units. Do not count these as newly validated relations.
5. **First possible code increment after acquired data:** one family-owned
   offline experiment reader and either a fixed-phase profile or bounded
   first-order fit, with synthetic numerical tests explicitly labeled as such.
   Use ordinary dataclasses/functions and existing research tooling. No runtime
   registration until a separate acceptance decision.
6. **Schema only if demonstrated necessary:** an explicit episode/phase reference,
   control/gain identity, fit domain and independent-validation record may be
   needed. Prefer existing fields; no generic schema engine or governance graph.
7. **Acceptance tests for that later increment:** unit dimensions, machine/circuit
   mismatch, missing phase, nonmonotonic time, aliasing/insufficient resolution,
   fit nonidentifiability, held-out repeatability, sensor and benign-context
   falsification, no calibration overwrite, no Step09/ticket authority changes.
8. **Tools:** existing Pint/SymPy/pydoe are sufficient offline. Keep explicit
   sqrt(JΣJᵀ). No new dependency, ML model, cloud path, DSP framework or additional
   physics package is justified by this review.

## 11. Evidence-strength changes

| Area | This literature/report pass | What a successful proposed experiment could add |
|---|---|---|
| Physics layer | Better measurement hypotheses and falsification plans; no status promotion | One source-defined residual with repeatability and a bounded domain |
| Exact-machine adaptation | No new calibrated machine or numerical change | Independent healthy calibration and held-out parameter stability |
| Real OSAT evidence | **No increase:** no new verified OSAT bytes | Only rights-approved, origin-verified actual OSAT observations count |
| Fault diagnosis | No causal proof | Controlled mechanism discrimination, still bounded by tested confounders |
| Model lifecycle | Clear proposal to separate fixed calibration from drift studies | Recalibration/holdout records for one experiment, not production qualification |
| Production testing | No pilot, certification or operational authority | Engineering-trial feasibility; prospective plant qualification remains future work |

An industrial analog may test parsing or a mathematical routine; it does not
validate an OSAT relation. A real semiconductor process-quality study is not
automatically a real equipment-failure study. Literature-supported plausibility,
observable deviation, diagnostic interpretation and causal failure evidence must
remain separate.

## 12. Highest-value next experiment

Choose **WS-01 validation of the existing current/speed residual** first, assuming
the project can obtain approved dicer access. It directly tests the only active
physical residual and can disprove an overly broad interpretation quickly.
Use one exact spindle/drive, a reference current measurement with explicitly
matched RMS/phase/filter semantics and independent speed reference. Start with
six approved speed plateaus, ten independent windows each, cold/warm blocks and
two sessions; hold tooling/coolant fixed, then introduce separately approved
context challenges. Record cut/no-cut phase and approved opaque context, not
recipes. Target controller-native current/speed capture with measured alignment;
100 Hz is a proposed starting request, not an asserted OEM export capability.
Freeze early healthy calibration and score the later session unchanged.

Ground truth is electrical/tach calibration, documented service/tool condition
and controlled engineering load/context, not a generated severity label. If safe
independent load variation is unavailable, call it a measurement/repeatability
study only. Plan half a day to one day plus metrology; at least 20 healthy samples
and six levels preserve the existing minimum, but those minima are not statistical
proof. Pass/fail bounds must be predeclared from uncertainty and engineering
resolution, not tuned to make the experiment succeed. Falsify usefulness when
benign feed/coolant/temperature variation explains residuals as strongly as the
independent condition, or later-day behavior is not reproducible. Do not change
the runtime equation or thresholds to rescue the result.

| Alternative | Value | Why not first / selection condition |
|---|---|---|
| WB-04 | Best new export route; deformation and inspected tool-life evidence can be valuable | Control/gain/tool-type semantics and destructive metrology are more demanding; choose first if only a suitable bonder is accessible |
| MO-01 | Potentially strong force-gap/vacuum/thermal experiments | Hot-tool, resin and coupled controls complicate access and falsification |
| FT-01 | Service-linked connector metrology could have direct asset value | Isolating contact path, force and DUT effects needs a qualified fixture |
| WS-01 | Validates the active relation and current acquisition contract | Preferred when real authorized equipment/reference instruments are available |

If no machine is available, the highest-value next action is the approved sample
export request, not implementing ten new candidates. No autonomous machine
control, fault probability or production-readiness claim follows from this report.
