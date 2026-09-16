# External real-data catalog

OSAT Fleet Command 0.2.5 extends the isolated **EXTERNAL REAL-DATA EVALUATION**
stage. This catalog records what was sought, what was locally inspected, what could be run
without changing the frozen 0.2.3 method, and why other sources were refused.
Raw datasets are never bundled. Keep approved local copies under ignored
`benchmarks/_external/<dataset-id>/`.

Schema compatibility is not provenance. A result is marked `real_data=true`
only when the supplied archive identity, canonical content hash, or complete
publisher checksum manifest matches an identity pinned from the authoritative
versioned record. Compatible but unmatched bytes are
`UNVERIFIED_EXTERNAL_INPUT`; malformed present bytes are `REJECTED_INVALID`.

Evidence classes are deliberately narrow:

- **A — TARGET SEMICONDUCTOR EQUIPMENT:** same target equipment type, but still
  not an OSAT plant validation unless the provenance actually establishes it.
- **B — OTHER SEMICONDUCTOR EQUIPMENT:** legitimate semiconductor data from a
  different process or task.
- **C — INDUSTRIAL PHYSICAL-MECHANISM ANALOG:** industrial equipment with a
  useful physical mechanism but not the target machine.
- **D — COMPONENT/PROCESS ANALOG:** a lower-level component or process analog.

No class B, C, or D result is target-machine validation. No public result below
is prospective OSAT plant validation, production qualification, a calibrated
failure probability, or maintenance authority.

Source status is reported separately from evaluator status:

- **EXECUTED + verified:** official bytes were checksum-verified and the stated
  deterministic inspection or evaluation ran.
- **AVAILABLE but not yet compatible:** raw bytes are downloadable, but size,
  dependencies, missing units, or incompatible semantics prevent execution.
- **UNAVAILABLE:** an expected artifact could not be obtained from its stated
  location.
- **REJECTED_INVALID:** supplied local bytes failed structural or provenance
  checks.
- **UNVERIFIED:** local bytes have no registered official identity.
- **PAPER_ONLY:** the publication is public but no raw telemetry is published.
- **REQUESTABLE_NONPUBLIC:** the publication explicitly permits a data request,
  but company-confidential bytes are not public.
- **EMBARGOED:** a repository record exists, but its attached full text or data
  are unavailable until the stated release date.

`DataOrigin` and evidence class are independent. `REAL_OSAT` means the source
provenance establishes an outsourced assembly/test facility; A/B/C/D describes
equipment relevance. No record is `REAL_OSAT` merely because it studies a
back-end semiconductor process.

## Snapshot 4 verified public-data additions

### STMicroelectronics ST-AWFD D1 and D2

The authoritative source is
[STMicroelectronics/ST-AWFD](https://github.com/STMicroelectronics/ST-AWFD),
commit `54be5cc91b83615240710bda9745f51c984d10c5`, licensed
CC BY-NC-SA 4.0. The evaluator pins the official archives separately:

- `st-awfd-d1` / `D1.zip`: SHA-256
  `97b2df4206177c5bc5b89ba18758215674bd437fef8c514320b831404f7674b7`;
- `st-awfd-d2` / `D2.zip`: SHA-256
  `e93d9f69ecb5c303f7f484647406d1ac2beda5726b99bb2984801867fea36297`.

Both contain the five reference fields `MaterialID`, `StepID`, `duration_ms`,
`target`, and `is_test`, followed by 15 anonymous normalized features for D1
and 20 for D2. `MaterialID` boundaries and the official `is_test` split are
preserved. Calibration uses only `is_test == 0` and `target == 0`, which means
normal-process benchmark data—not independently confirmed healthy machine
history. Per MaterialID and supplied headline StepID, each anonymous feature
produces a median (`kind="location"`) and MAD (`kind="spread"`). No slope is
calculated because `duration_ms` is normalized process-step time. Each StepID
is fit independently with the unchanged Step07 center/scale calculation; D1
and D2 never share models.

The pinned D1 bytes contain 602,108 data rows, 5,104 MaterialIDs and StepIDs
`-2, -1, 1, 2, 4, 6, 7`. This differs from the repository README's 5,105
MaterialIDs and mandatory StepID 5. Snapshot 4 retains the specified headline
set `2, 4, 5, 6, 7`, reports StepID 5 as `NO_SOURCE_ROWS`, reports optional
`-1/-2` coverage descriptively, and does not relabel StepID 1. On 1,807
held-out MaterialIDs (2 abnormal), the location score has AUROC
`0.935180055401662` and average precision `0.012303436225975538`.
Material scoring coverage is `1.0`, headline-step coverage is `4/5 = 0.8`, and
complete-headline-material coverage is `0.0` because StepID 5 is absent. The
positive prevalence and AP baseline are `2/1807 = 0.0011068068622025456`; AP
lift over prevalence is `11.1161546301689`. This is marked
`LOW_POSITIVE_COUNT_DESCRIPTIVE_ONLY`: an AUROC based on two abnormal held-out
MaterialIDs is statistically fragile.

The pinned D2 bytes contain 126,794 data rows and 1,156 MaterialIDs, one below
each README value, with supplied mandatory StepIDs 1 and 2. On 604 held-out
MaterialIDs (367 abnormal), the location score has AUROC and average precision
of `1.0`. These values are reported as observed, without threshold tuning.
Material, headline-step, and complete-headline-material coverage are all `1.0`.
Positive prevalence and AP baseline are `367/604 = 0.6076158940397351`, giving
an AP lift over prevalence of `1.645776566757493`.

Static probes of the frozen numeric thresholds 0.35, 0.60, and 0.82 report
confusion counts, precision, recall, F1, balanced accuracy, and MCC. They are
not health states. Anonymous z-scaled columns receive no physical-channel or
canonical-station mapping; there is no machine identity, Step01 physics,
Step05, Step09 chronology/hysteresis, Step10/15 authority, or OSAT-validation
claim. The labels identify abnormal MaterialIDs/process outcomes, not confirmed
maintenance faults. Raw and sample-level transformed data remain ignored and
uncommitted.

For both datasets, the deterministic interpretation is that external evidence
supports Step07 continuous discrimination on this benchmark, while transfer or
calibration of the frozen Step09 thresholds is not supported. The thresholds
remain unchanged. ST-AWFD is classified as a
`NONCOMMERCIAL_RESEARCH_BENCHMARK` under CC BY-NC-SA 4.0. Commercial
re-execution or redistribution requires permission or legal/license review.
That dataset license does not by itself make a claim that Fleet Command source
code is ShareAlike.

### TUHH DISCO DAD3350 diced-surface maps

The authoritative v1.0 source is DOI
[10.15480/882.15763](https://doi.org/10.15480/882.15763), with the precise
rights statement `Public Domain Mark 1.0` (not CC0). Pinned
source identities are:

- `data_raw.zip`: SHA-256
  `8dc6cd61c837100a0e5e9b7877e6b6c7e5bbde2f70e08017d48c4f0577125dca`,
  publisher MD5 `e559d1736e23898b9d29e85b7f0ab3ed`;
- `README.txt`: SHA-256
  `fdb9112d2061afef6b3af38647ef3ec10729983f9b159a978e7a5adc5d97715f`,
  publisher MD5 `48d7f327a2d6068d8a130436762f1a20`.

The archive contains exactly six VK7 maps at feed velocities 0.1, 0.2, 0.5,
0.7, 1, and 5 mm/s. The source records a DISCO DAD3350, 1-mm-thick/100-mm
fused-silica wafer, 30,000-rpm spindle, and DISCO R07-SDC600-BB101-75 blade.
The optional parser is `convert-keyence-files` 0.1.0 at commit
`36e1eb9f550a41f5be2369de125ec51338f54d9e` (Unlicense). `surfalize` is not
used because its current GPL terms are unsuitable here.

All six 768×1024 maps parsed successfully. Snapshot 4 reports only dimensions,
valid-pixel fraction, median height, robust spread, detrended height RMS,
detrended mean absolute deviation, peak-to-valley, and per-statistic Spearman
association with feed velocity. Detrended quantities are descriptive proxies
unless independently validated against Keyence VK-A3D output; no ISO roughness
compliance is claimed. This is real target-equipment/process evidence, not
equipment-health validation or OSAT evidence. Steps 07/09/10/15 are not run.
Cross-map absolute median-height association is marked
`DATUM_COMPARABILITY_UNVERIFIED` and is not headline physics evidence. The
principal descriptive results are detrended RMS, detrended mean absolute
deviation, and peak-to-valley.

The deterministic third-party data-use and parser inventory is
[`THIRD_PARTY_DATA_USE.json`](../resources/THIRD_PARTY_DATA_USE.json).

### CHDL disposition

The official arXiv v1 source for
[2507.06738](https://arxiv.org/abs/2507.06738) describes CHDL but supplies no
working dataset/repository URL; its rendered contribution links are malformed
placeholders. No authoritative dataset bytes could therefore be pinned.
CHDL remains catalog-only. No vision model is added, and image intensity is not
converted into telemetry.

## Historical 0.2.4 executable and inspected sources

The following entries preserve the 0.2.4 evaluation record. They are no longer
the complete current CLI registry order because Snapshot 4 adds the three
datasets above.

1. **Chang/Tsai/Mo wafer dicing (A)** — DOI
   [10.3390/electronics13101802](https://doi.org/10.3390/electronics13101802).
   Bao Rong Chang, Hsiu-Fen Tsai, and Hsiang-Yu Mo (2024), *Ensemble
   Meta-Learning-Based Robust Chipping Prediction for Wafer Dicing*.
   The paper describes two DISCO DFD6560 machines, spindle current, three water
   flows, three gas signals, and chipping classes. Its public data statement
   links a Google Drive folder described as “Sample Programs for Sample
   Program.zip.” That folder returned HTTP 404 during the Snapshot 3 attempt;
   no authoritative raw measurement artifact with source schema, units,
   machine/run identities, and labels was obtainable. The source says only
   “a semiconductor company in Kaohsiung, Taiwan,” so OSAT provenance is not
   established. Reported fields include post-run `SpindleCurrent_Z1/Z2`, water
   flow/status, and air pressure; spindle-current units and synchronized spindle
   speed are absent. Chipping is a process-quality label, not a maintenance
   fault. **Origin: EXTERNAL_BENCHMARK. Raw-data status/execution: PAPER_ONLY;
   not run. Mapping: impossible without units, raw run boundaries, and speed.**

2. **PHM Society 2018 Ion Mill (B)** — official
   [challenge page](https://phmsociety.org/conference/annual-conference-of-the-phm-society/annual-conference-of-the-prognostics-and-health-management-society-2018-b/phm-data-challenge-6/)
   and [NASA mirror record](https://c3.ndc.nasa.gov/dashlink/resources/1009/).
   This is real wafer-fabrication equipment with tool/time/fault boundaries,
   but the official description explicitly says the data are anonymized and
   units are not provided. The available files total multiple gigabytes. Exact
   unit-enforced OSAT or ephemeral channel mapping is therefore impossible.
   Label semantics are tool/time fault scenarios, not OSAT maintenance records.
   **Origin: EXTERNAL_BENCHMARK. Equipment: wafer-fabrication ion mill; OSAT:
   no. Raw-data status: AVAILABLE but not yet compatible. Mapping: none without
   units. Execution: not downloaded or run. Limitation: multi-gigabyte source.**

3. **PHM Society 2016 CMP (B)** — official
   [challenge page](https://phmsociety.org/conference/annual-conference-of-the-phm-society/annual-conference-of-the-prognostics-and-health-management-society-2016/phm-data-challenge-4/).
   The page documents wafer/run/stage boundaries, 25 process fields, and a
   separate continuous material-removal-rate target. The legacy official ZIP
   links returned a not-found page during the release attempt. CMP rotation,
   pressure, slurry, and usage variables are not wafer-saw, molding, or other
   canonical OSAT channels. The label is continuous material-removal rate, not
   machine health. **Origin: EXTERNAL_BENCHMARK. Equipment: wafer-fabrication
   CMP; OSAT: no. Raw-data status: UNAVAILABLE at the legacy links. Mapping:
   none. Execution: not run; local artifacts remain inspectable.**

4. **FORinFPRO-HIMD (C)** — DOI
   [10.5281/zenodo.20744054](https://doi.org/10.5281/zenodo.20744054).
   All three v1 files and their publisher MD5 identities were inspected:
   `cycle_001_machine_data.csv`, `cycle_001_pt.csv`, and
   `cycle_001_us_rms.csv`. They contain one polymer
   hybrid-injection-molding cycle. The CSV headers do not declare units, and
   polymer injection molding is not semiconductor transfer molding. With no
   exact unit mapping and no disjoint baseline/evaluation cycles, the evaluator
   reports schema/coverage only.
   **Authors/year:** Rohan Kini and Lukas Schweizer (2026). **Origin:**
   EXTERNAL_BENCHMARK; OSAT: no. **Relevant channels:** 62 candidate machine,
   process-tomography, and ultrasonic fields; units/semantics are insufficient
   for exact canonical mapping. **Label:** one process cycle, no health label.
   **Status:** EXECUTED + verified for deterministic schema inspection;
   evaluator status `INSPECTED_NOT_EXECUTABLE`. **Limitation:** no disjoint
   confirmed-healthy/evaluation runs.

5. **R2R Web Tension (C)** — DOI
   [10.17632/gz3rzw6xgf.2](https://doi.org/10.17632/gz3rzw6xgf.2) and the
   associated [method paper](https://link.springer.com/article/10.1007/s10845-024-02488-y).
   The public v2 `dataset.zip` (SHA-256
   `3168a831e38c9388e73ba809661c282b560640ea269beba5d976340eb5e1ac16`)
   was retrieved and its aggregate workbook plus 210 sensor workbooks were
   inspected without adding a spreadsheet dependency. Four raw fields have
   exact physical names and units: `Film Tension #1 (kg)`, `Film Tension #2
   (kg)`, `Film Tension #3 (kg)`, and `Web Current Speed (mm/sec)`. They map to
   four ephemeral `web_transport` benchmark channels. The pinned sensor schema
   contains 33 inspected fields: 20 physical-valued fields, four explicit
   metadata/label fields (`Date`, `Model`, `Trigger`, `Film kind`), and nine
   `OutFeeder-Control:`/`ReWinder-Control:` configuration fields. Headline
   channel coverage is therefore 4/20 (0.20), not 4/4. Controller settings,
   material geometry, and derived aggregates are not mapped. Because the data
   are operating-point experiments without health labels or confirmed-healthy
   exact-machine history, no Step 07/09/10 result is reported.
   **Authors/year:** Anton Gafurov, Jaeyoung Kim, Inyoung Kim, and Taik-Min Lee
   (2024 dataset release).
   **Origin:** EXTERNAL_BENCHMARK; OSAT: no. **Raw-data/execution status:**
   EXECUTED + verified for deterministic schema inspection; evaluator status
   `INSPECTED_NOT_EXECUTABLE`. **Mapping feasibility:** four exact ephemeral
   analog mappings only. **Limitation:** no health, fault, alarm, or maintenance
   labels.

6. **ME-AD (C)** — DOI
   [10.5281/zenodo.20817531](https://doi.org/10.5281/zenodo.20817531).
   This is real progressive joint-3 gearbox damage on a Mitsubishi RV-7FM
   robot, with predefined task splits and torque/position/velocity signals.
   The sole archive is about 10.8 GB, and torque is not motor current. It was
   not downloaded for this lightweight release. **Authors/year:** Giulio
   Giacomuzzo et al. (2026). **Origin:** EXTERNAL_BENCHMARK; OSAT: no. **Raw-data
   status:** AVAILABLE but not yet compatible. **Labels:** staged gearbox-damage
   progression, not OSAT maintenance ground truth. **Mapping:** none because
   torque is not motor current. **Execution:** not run; local-path inspection
   remains fail-closed and unverified. **Limitation:** 10.8 GB archive.

7. **KUKA KR3 motor current (D)** — DOI
   [10.5281/zenodo.21456277](https://doi.org/10.5281/zenodo.21456277).
   The complete official 25.9 MB ZIP was run. Six source columns map exactly:

   - `Iststrom_A1 (A)` → `motor_current_a1`, unit `A`, subsystem `axis_a1`
   - `Iststrom_A2 (A)` → `motor_current_a2`, unit `A`, subsystem `axis_a2`
   - `Iststrom_A3 (A)` → `motor_current_a3`, unit `A`, subsystem `axis_a3`
   - `Iststrom_A4 (A)` → `motor_current_a4`, unit `A`, subsystem `axis_a4`
   - `Iststrom_A5 (A)` → `motor_current_a5`, unit `A`, subsystem `axis_a5`
   - `Iststrom_A6 (A)` → `motor_current_a6`, unit `A`, subsystem `axis_a6`

   `Sample` is checked only for finite monotonic source order. Physical-signal
   channel coverage is 6/6; source-field coverage is 6/7 when that field is
   counted. The v1 archive SHA-256, publisher MD5, and canonical 128-CSV content
   hash are pinned; compatible unmatched directories are not declared real.
   `FULL_STATION_REPRESENTATION=false`: these channels live in an
   ephemeral `external_kuka_kr3` profile and are never substituted into a
   canonical OSAT station. Complete files preserve robot/run boundaries and
   the published same-machine splits: R1 D1–D3 calibrates an explicitly
   nominal workload baseline and D4 is evaluated; R2 uses D5–D7 and D8.

   Independent CSVs are not assigned a cross-run chronology. Step 09
   hysteresis and Step 10 evidence are therefore not run, and no health-state
   distribution is reported. The unresolved 12 ms documentation versus
   Sample-increment discrepancy makes trend features assumption-dependent, so
   only Step 02 location/spread statistics enter the pure Step 07 run-level
   numerical deviation score. One CSV is one external run-level window, not
   the operational 60-second window. Payload/deviation association, score
   distribution, coverage, and runtime are reported—never accuracy. The
   nominal baseline is not represented as confirmed healthy history.
   **Authors/year:** Adam Bátrla, Radim Hercík, Radek Byrtus, and Ojan
   Majidzadeh Gorjani (2026). **Origin:**
   EXTERNAL_BENCHMARK; OSAT: no. **Raw-data/execution status:** EXECUTED +
   verified. **Labels:** payload/workload only. **Limitation:** payload is not
   degradation, failure, or maintenance ground truth.

8. **RDDAC (C)** — DOI
   [10.18419/DARUS-5589](https://doi.org/10.18419/DARUS-5589) and
   [dataset documentation](https://rddac.readthedocs.io/).
   Real forming/cutting force series and official machine/run splits are
   relevant mechanism analogs. The full release is roughly 87 GB; even the
   small sample is about 174 MB and uses an HDF5 path not present in the pinned
   dependencies. No new dependency or partial proxy mapping was introduced.
   **Authors/year:** Sebastian Baum and Pascal Heinzelmann (2026). **Origin:**
   EXTERNAL_BENCHMARK; OSAT: no. **Raw-data status:** AVAILABLE but not yet
   compatible. **Relevant channels/labels:** forming/cutting force with official
   machine/run splits; no exact canonical mapping. **Execution:** not run.

9. **NASA/UC Berkeley Milling (C)** — official
   [NASA Open Data record](https://data.nasa.gov/dataset/milling-wear).
   The official ZIP was run through the existing isolated descriptive parser:
   167 runs, 16 cases, 146 finite flank-wear values. `smcAC`, `smcDC`, and
   `vib_spindle` output units are undocumented, and the struct has no
   spindle-speed time series. Coverage into unit-enforced pipeline channels is
   0/3; no Step 02/03/07/09 health path is fabricated. Supported output is
   continuous wear rank association and runtime only.
   **Authors/year:** UC Berkeley BEST Lab / NASA PCoE public repository record.
   **Origin:** EXTERNAL_BENCHMARK; OSAT: no. **Raw-data/execution status:**
   EXECUTED + verified. **Label:** continuous measured flank wear. **Mapping:**
   0/3 because signal-output units are undocumented and speed is absent.

10. **UCI SECOM (B)** — DOI
    [10.24432/C54305](https://doi.org/10.24432/C54305).
    The complete official ZIP was inspected: 1,567 rows, 590 anonymized
    variables, 1,463 pass and 104 fail-yield labels. Exact channel coverage is
    0/590 because variables have no physical names or units. Yield is not
    equipment health, so no model, accuracy, or maintenance result is emitted.
    **Authors/year:** McCann and Johnston (2008 repository release). **Origin:**
    EXTERNAL_BENCHMARK; OSAT: not established. **Raw-data/execution status:**
    EXECUTED + verified for deterministic inspection; evaluator status
    `INSPECTED_NOT_EXECUTABLE`. **Label:** process pass/fail yield only.
    **Mapping:** impossible because names and units are anonymized.

## Genuine OSAT research leads

### PTI / Powertech production wire bonding

Chin Ta Wu, Shing Han Li, and Ching Shih Tsou (2026), *Integrating FDC and
Machine Learning for Enhanced Anomaly Detection in WB Bonding Joint Quality*,
DOI [10.32604/cmc.2026.078762](https://doi.org/10.32604/cmc.2026.078762).
The paper identifies Powertech Technology Inc. and explicitly says its empirical
records came from wire-bond machines in an OSAT facility. It reports October
2024 training and November-December 2024 evaluation across Recipes A-D, totaling
5,612,310 IC-level records. Fields are Capillary Count, Bond Height Delta,
Deformation, Die Height, Die Tilt, Bond Force, USG Impedance, USG Current, Z at
Contact, and Z at End of Bonding. MES scrap and machine alarms were used to
exclude records from the nominal training set; production-line inspections
labelled bond-joint quality anomalies. None of those labels is confirmed
machine-fault or maintenance ground truth.

The publisher article, PDF, DOI metadata, directly associated search results,
and obvious repository/supplement paths exposed no public data attachment. The
publication does not state engineering units, and its availability statement
says company-confidential datasets are available from the corresponding author
on reasonable request. **Published study setting: REAL_OSAT. Executable data
origin: not assigned because no source bytes were obtained. Equipment:
production wire bonder / WB-04 candidate. Raw-data/execution status:
REQUESTABLE_NONPUBLIC; not executed. Potential evidence class if verified: A.
Mapping feasibility: possible only after exact units and acquisition semantics
are supplied; no current field is mapped.** In particular,
USG Impedance does not revive the rejected Step 01 impedance relation: the
required synchronized voltage, current, phase, and bond timing are absent.
The minimum de-identified request is specified in
[`REAL_OSAT_DATA_REQUEST.md`](REAL_OSAT_DATA_REQUEST.md).

### PTI / Powertech production dicing inspection imagery

Chin Ta Wu, Ching Shih Tsou, and Shing Han Li (2023), *Data Augmentation With CycleGAN to Build a
Classifier for Novel Defects From the Dicing Stage of Semiconductor Package
Assembly*, DOI
[10.1109/ACCESS.2023.3309159](https://doi.org/10.1109/ACCESS.2023.3309159).
The author manuscript describes 3,125 production defect images (2,186 training,
939 test) and 1,224 generated training images. Direct DOI, DOAJ, author-copy,
supplement, and obvious repository checks exposed no downloadable original or
de-identified production image dataset. The paper also describes customer-IP
constraints. **Published study setting: REAL_OSAT. Evidence type:
process-quality/inspection imagery, not machine telemetry or machine-health
validation. Raw-data/execution status: REQUESTABLE_NONPUBLIC; not obtained or
executed. Potential evidence class if verified: A. Canonical mapping: none.**
No vision, CNN, or CycleGAN path is added to the product.

### ASE production wire-bond AOI imagery

Ching-Chao Hsu (2025), *AOI-Based Defect Detection in the Wire Bonding
Process*, National Sun Yat-sen University thesis repository record
[`etd-0609125-111038`](https://ethesys.lis.nsysu.edu.tw/ETD-db/ETD-search-c/view_etd?URN=etd-0609125-111038).
The public metadata says ASE Semiconductor supplied single-layer aluminum-pad
wire-bond products. The repository reports zero downloads and embargoes the
full text until 2035-07-09; no linked attachment or data repository was
available. **Published study setting: REAL_OSAT. Evidence type:
process-quality/AOI imagery, not equipment telemetry. Raw-data/execution
status: EMBARGOED/PAPER_ONLY; not obtained or executed. Potential evidence
class if verified: A. Canonical mapping: none.** No public sample count is
claimed for this embargoed wire-bond thesis.

### ASE drilling-process AOI dataset

The separate ASE-provided drilling dataset is described by arXiv
[2404.05183](https://arxiv.org/abs/2404.05183) and IEEE ICCE 2025 DOI
[10.1109/ICCE63647.2025.10930135](https://doi.org/10.1109/ICCE63647.2025.10930135).
It contains 455 drilling/AOI samples: 225 normal and four defect classes of 92,
44, 50, and 44. These counts do not belong to the wire-bond thesis. This is
genuine ASE-provided process-inspection evidence, not wire-bond telemetry or
equipment-health validation. No authoritative raw dataset bytes were located,
so it remains publication-only and non-executed.

### UTAC smart-manufacturing wafer-saw evidence

UTAC's official
[2023 Sustainability Report](https://utacgroup.com/wp-content/uploads/2025/04/UTAC_Sustainability_Report_2023.pdf)
documents DISCO wafer-saw equipment, machine-log capture, FDC/data mining,
predictive alerts and maintenance, and machine-alarm remote monitoring. A
narrow check of the report and directly associated public materials exposed no
downloadable machine-log dataset or linked research repository. **Corporate
REAL_OSAT operational evidence only; no executable data origin is assigned.
Equipment: production wafer saw / WS-01 research lead. Raw-data/execution
status: REQUESTABLE_NONPUBLIC; not executed. Potential evidence class if
verified: A.** A UTAC/WS-01-specific de-identified request is retained in
`REAL_OSAT_DATA_REQUEST.md`.

### 2026 SiC wafer-dicing current/speed experiment

Yufang Wang et al. (2026), *Processing Characteristics of Ultra-Precision
Cutting of 4H-SiC Wafers by Dicing Blade*, DOI
[10.3390/mi17020187](https://doi.org/10.3390/mi17020187). The study reports
dicing experiments at 22,000, 26,000, 30,000, 34,000, and 38,000 RPM and
spindle-inverter current in amperes acquired at approximately 20 Hz. The
article says its original data are included in the article, but the public
article exposes figures and summarized measurements rather than a
machine-readable raw current trace or separate data attachment. **Origin:
real semiconductor-equipment physical evidence; OSAT not established.
Evidence type: physics-supporting current/speed experiment, not health or
maintenance validation. Raw-data/execution status: PAPER_ONLY; not executed.
Canonical mapping: none.** This strengthens only the research trail behind the
existing WS-01 hypothesis; the frozen Step01 equation is unchanged.

### ATEP / Amkor Portugal auxiliary vacuum pumps

Tiago Narciso da Costa Fernandes (2022), *Implementação de manutenção preditiva
numa indústria de semicondutores*, ISEP master's dissertation,
[hdl:10400.22/20698](http://hdl.handle.net/10400.22/20698). The public thesis
establishes work at ATEP - Amkor Technology Portugal, S.A. and describes two
liquid-ring vacuum-pump monitoring systems. The offline system collected
three-axis acceleration and temperature; the online system recorded velocity
(mm/s), acceleration (m/s²), sound (dB), pressure (mbar), humidity (%rH), and
temperature (°C). The thesis describes a later pump failure and daily Excel
samples, but the repository exposes only the 135-page PDF, not the text/Excel or
cloud telemetry, machine-readable boundaries, or maintenance record.

**Published source setting: REAL_OSAT. Executable data origin: not assigned
because no telemetry bytes were published. Equipment: auxiliary liquid-ring
vacuum pump, not a canonical production station. Raw-data/execution status:
PAPER_ONLY; not executed. Potential evidence class: C (auxiliary
rotating-equipment mechanism analog).
Mapping: none; no new canonical station is added. Label status: narrative pump
failure, not an independently adjudicated machine-readable interval.**

## Other relevant sources that were not executable

- **Wire bond:** real NXP machine-signal/AOI work is documented in
  [Interpretable chip-quality classification with signal and feature selection in wire bonding](https://link.springer.com/article/10.1007/s10696-025-09621-w),
  but its data-availability statement says company production data cannot be
  shared. A separate [OSAT FDC study](https://www.sciencedirect.com/org/science/article/pii/S1546221826004364)
  describes bond force, ultrasonic current/impedance, and capillary-count data
  but does not publish the raw OSAT records. Public wire-continuity test data
  for [implantable-sensor packages](https://doi.org/10.15129/f9eb43b5-9d4b-49fc-ad53-f565f03bfc78)
  measure package test structures, not wire-bonder equipment health.

- **Die bond / die attach:** the public literature and
  [defect-detection survey](https://arxiv.org/abs/2206.07481) concern bond
  quality or images. No public, source-identified die-attach motor/vacuum
  telemetry with exact-machine health history and maintenance events was found.

- **Laser marking:** public laser data found during the search concern additive
  manufacturing tracks or optical mark quality, not semiconductor laser-marker
  delivered power, drive current, galvo current/error, and maintenance events.
  No exact station mapping was justified.

- **Semiconductor molding:** public
  [injection-molding production data](https://b2share.eudat.eu/records/k0v7s-jf859)
  and FORinFPRO-HIMD use polymer research machines and mostly part-quality or
  process labels. They do not establish semiconductor transfer-mold equipment
  identity, units for all required channels, or maintenance ground truth.

- **Wafer/prober:** the public
  [CMU Wafer database](https://www.cs.cmu.edu/~bobski/data/data.html) is a
  wafer-fabrication vacuum-chamber-sensor classification corpus, not prober
  equipment health. Published wafer-prober motion research describes
  proprietary industrial signals, while public wafer-level characterization
  data concern DUT electrical results. Wafer maps and device measurements are
  also process/product IP outside the approved PHM ingestion boundary.

- **Final test / ATE:** public material describes STDF device-test/yield data,
  not socket/contact/handler health with exact maintenance events. Device test
  programs, bins, limits, and wafer maps are product/process information that
  must not be ingested as substitute equipment-health telemetry. No reviewed
  public final-test equipment-health dataset was found.

## Run and report

```powershell
.venv\Scripts\python -m osat_edge.ui.cli evaluate-real --dataset kuka-kr3 --path benchmarks\_external\kuka-kr3
.venv\Scripts\python -m osat_edge.ui.cli evaluate-real --dataset st-awfd-d1 --path benchmarks\_external\st-awfd-d1
.venv\Scripts\python -m osat_edge.ui.cli evaluate-real --dataset st-awfd-d2 --path benchmarks\_external\st-awfd-d2
.venv\Scripts\python -m osat_edge.ui.cli evaluate-real --dataset tuhh-dad3350-surface --path benchmarks\_external\tuhh-dad3350-surface
.venv\Scripts\python -m osat_edge.ui.cli evaluate-real --all --root benchmarks\_external
.venv\Scripts\python -m osat_edge.ui.cli evaluate-real --all --root benchmarks\_external --report
.venv\Scripts\python -m osat_edge.ui.cli verify-real-evidence --root benchmarks\_external
```

Without `--report`, no artifact is written. With it, the comparison is written
to `.artifacts/real_data/comparison.json`. Runtime measurements remain in CLI
output but are removed from this deterministic scientific artifact. A small
current aggregate result is retained at
`post04_real_data_evaluation/resources/0.2.5-real-data.json`; it contains no raw
records or sample-level transformed features. The existing
`0.2.4-real-data.json` remains byte-immutable historical evidence.
`verify-real-evidence` performs no download. It first verifies historical
artifact byte integrity, then separately regenerates the current 0.2.5
comparison and checks its report/evaluator identities. A changed 0.2.5
evaluator hash is not described as drift from the historical 0.2.4 evaluator.
External data never enter the HMI,
operational `MachinePipeline`, family-model trainer, maintenance database, RAG,
LLM, or ticket stage.
