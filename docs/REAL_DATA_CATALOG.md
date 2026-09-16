# External real-data catalog

OSAT Fleet Command 0.2.4 is an **EXTERNAL REAL-DATA EVALUATION** release. This
catalog records what was sought, what was locally inspected, what could be run
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

## Executable and inspected sources

The release attempt order is the CLI registry order.

1. **Chang/Tsai/Mo wafer dicing (A)** — DOI
   [10.3390/electronics13101802](https://doi.org/10.3390/electronics13101802).
   The paper describes two DISCO DFD6560 machines, spindle current, three water
   flows, three gas signals, and chipping classes. Its public data statement
   links a Google Drive folder described as “Sample Programs for Sample
   Program.zip”; no authoritative raw measurement artifact with source schema,
   units, machine/run identities, and labels was obtainable. **Not run.**

2. **PHM Society 2018 Ion Mill (B)** — official
   [challenge page](https://phmsociety.org/conference/annual-conference-of-the-phm-society/annual-conference-of-the-prognostics-and-health-management-society-2018-b/phm-data-challenge-6/)
   and [NASA mirror record](https://c3.ndc.nasa.gov/dashlink/resources/1009/).
   This is real wafer-fabrication equipment with tool/time/fault boundaries,
   but the official description explicitly says the data are anonymized and
   units are not provided. The available files total multiple gigabytes. Exact
   unit-enforced OSAT or ephemeral channel mapping is therefore impossible.
   **Not downloaded or run.**

3. **PHM Society 2016 CMP (B)** — official
   [challenge page](https://phmsociety.org/conference/annual-conference-of-the-phm-society/annual-conference-of-the-prognostics-and-health-management-society-2016/phm-data-challenge-4/).
   The page documents wafer/run/stage boundaries, 25 process fields, and a
   separate continuous material-removal-rate target. The legacy official ZIP
   links returned a not-found page during the release attempt. CMP rotation,
   pressure, slurry, and usage variables are not wafer-saw, molding, or other
   canonical OSAT channels. **Not run; local artifacts remain inspectable.**

4. **FORinFPRO-HIMD (C)** — DOI
   [10.5281/zenodo.20744054](https://doi.org/10.5281/zenodo.20744054).
   All three v1 files and their publisher MD5 identities were inspected:
   `cycle_001_machine_data.csv`, `cycle_001_pt.csv`, and
   `cycle_001_us_rms.csv`. They contain one polymer
   hybrid-injection-molding cycle. The CSV headers do not declare units, and
   polymer injection molding is not semiconductor transfer molding. With no
   exact unit mapping and no disjoint baseline/evaluation cycles, the evaluator
   reports schema/coverage only.

5. **R2R Web Tension (C)** — DOI
   [10.17632/gz3rzw6xgf.2](https://doi.org/10.17632/gz3rzw6xgf.2) and the
   associated [method paper](https://link.springer.com/article/10.1007/s10845-024-02488-y).
   The public v2 `dataset.zip` (SHA-256
   `3168a831e38c9388e73ba809661c282b560640ea269beba5d976340eb5e1ac16`)
   was retrieved and its aggregate workbook plus 210 sensor workbooks were
   inspected without adding a spreadsheet dependency. Four raw fields have
   exact physical names and units: `Film Tension #1 (kg)`, `Film Tension #2
   (kg)`, `Film Tension #3 (kg)`, and `Web Current Speed (mm/sec)`. They map to
   four ephemeral `web_transport` benchmark channels. Controller settings,
   material geometry, and derived aggregates are not mapped. Because the data
   are operating-point experiments without health labels or confirmed-healthy
   exact-machine history, no Step 07/09/10 result is reported.

6. **ME-AD (C)** — DOI
   [10.5281/zenodo.20817531](https://doi.org/10.5281/zenodo.20817531).
   This is real progressive joint-3 gearbox damage on a Mitsubishi RV-7FM
   robot, with predefined task splits and torque/position/velocity signals.
   The sole archive is about 10.8 GB, and torque is not motor current. It was
   not downloaded for this lightweight release. **Not run; supported as an
   explicitly reported local-path inspection only.**

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

8. **RDDAC (C)** — DOI
   [10.18419/DARUS-5589](https://doi.org/10.18419/DARUS-5589) and
   [dataset documentation](https://rddac.readthedocs.io/).
   Real forming/cutting force series and official machine/run splits are
   relevant mechanism analogs. The full release is roughly 87 GB; even the
   small sample is about 174 MB and uses an HDF5 path not present in the pinned
   dependencies. No new dependency or partial proxy mapping was introduced.
   **Not run.**

9. **NASA/UC Berkeley Milling (C)** — official
   [NASA Open Data record](https://data.nasa.gov/dataset/milling-wear).
   The official ZIP was run through the existing isolated descriptive parser:
   167 runs, 16 cases, 146 finite flank-wear values. `smcAC`, `smcDC`, and
   `vib_spindle` output units are undocumented, and the struct has no
   spindle-speed time series. Coverage into unit-enforced pipeline channels is
   0/3; no Step 02/03/07/09 health path is fabricated. Supported output is
   continuous wear rank association and runtime only.

10. **UCI SECOM (B)** — DOI
    [10.24432/C54305](https://doi.org/10.24432/C54305).
    The complete official ZIP was inspected: 1,567 rows, 590 anonymized
    variables, 1,463 pass and 104 fail-yield labels. Exact channel coverage is
    0/590 because variables have no physical names or units. Yield is not
    equipment health, so no model, accuracy, or maintenance result is emitted.

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
.venv\Scripts\python -m osat_edge.cli evaluate-real --dataset kuka-kr3 --path benchmarks\_external\kuka-kr3
.venv\Scripts\python -m osat_edge.cli evaluate-real --all --root benchmarks\_external
.venv\Scripts\python -m osat_edge.cli evaluate-real --all --root benchmarks\_external --report
```

Without `--report`, no artifact is written. With it, the comparison is written
to `.artifacts/real_data/comparison.json`. Runtime measurements remain in CLI
output but are removed from this deterministic scientific artifact. A small
auditable release result is retained at
`benchmarks/results/0.2.4-real-data.json`; it contains no raw dataset records.
External data never enter the HMI,
operational `MachinePipeline`, family-model trainer, maintenance database, RAG,
LLM, or ticket stage.
