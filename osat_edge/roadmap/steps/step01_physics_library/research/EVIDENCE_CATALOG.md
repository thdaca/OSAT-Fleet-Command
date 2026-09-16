# Step01 research-evidence catalog

This catalog classifies literature and prospective data access. It does not
create a `DataOrigin`, approve source bytes, score a machine, or raise evidence
maturity. A paper is never treated as raw telemetry.

## Evidence tiers

- `PUBLISHED_REAL_OSAT_STUDY`: a published source documents work in a real OSAT
  setting. It may contain only narrative, figures, or summarized results.
- `REQUESTABLE_REAL_OSAT_DATA`: the source explicitly states that confidential
  real-OSAT records may be requested. No data is considered obtained until
  approved bytes are received and verified through the normal provenance path.
- `EXECUTED_REAL_OSAT_DATA`: approved real-OSAT bytes have actually been
  verified and evaluated. No Step01 source currently has this tier.

These are research classifications only. They are deliberately absent from the
operational `DataOrigin` enum.

## Real-OSAT and real-semiconductor evidence

### PTI / Powertech production wire bonding

- Classification: `PUBLISHED_REAL_OSAT_STUDY` and
  `REQUESTABLE_REAL_OSAT_DATA`; target `WB-04`.
- Source: DOI [10.32604/cmc.2026.078762](https://doi.org/10.32604/cmc.2026.078762).
- The study identifies Powertech Technology Inc. and real OSAT wire-bond
  production. Its exact fields are Capillary Count, Bond Height Delta,
  Deformation, Die Height, Die Tilt, Bond Force, USG Impedance, USG Current,
  Z at Contact, and Z at End of Bonding.
- The availability statement says company-confidential datasets are available
  from the corresponding author on reasonable request.
- Boundary: no public raw records or engineering units were obtained. Inspection
  outcomes are not automatically equipment-fault labels. `USG Impedance` is a
  machine field whose definition is unknown, not a reconstructed `V/I` quantity.

### Amkor Portugal / ATEP auxiliary vacuum pumps

- Classification: `PUBLISHED_REAL_OSAT_STUDY`; auxiliary/noncanonical.
- Source: Tiago Fernandes (2022),
  [hdl:10400.22/20698](https://hdl.handle.net/10400.22/20698).
- The public full thesis describes actual sensor monitoring, an observed pump
  failure after deployment, and two years of maintenance history. The online
  system measured velocity (mm/s), acceleration (m/s²), sound (dB), pressure
  (mbar), humidity (%rH), and temperature (°C). Vibration velocity showed the
  clearest pre-failure progression; abnormal behavior appeared approximately
  11 January before failure on 15 January.
- The reported two-year history contains 5 failures / about 145-day MTBF for
  WLPBSG-0004 and 11 failures / about 66-day MTBF for WLPGMP-0005.
- Boundary: these are published study results. The public record does not expose
  the raw time series; no canonical station, runtime score, or executable OSAT
  evidence is created.

### ASE wire-bond process inspection thesis

- Classification: `PUBLISHED_REAL_OSAT_STUDY`; noncanonical process evidence.
- Source: Ching-Chao Hsu (2025), *AOI-Based Defect Detection in the Wire Bonding
  Process*, record `etd-0609125-111038`.
- The public repository record describes genuine ASE-provided wire-bond
  process/inspection samples, but the full thesis is embargoed until 2035.
- Boundary: no public sample count or raw download is established. These are
  process/AOI samples, not equipment-health telemetry or maintenance evidence.

### ASE drilling-process AOI study

- Classification: published real-semiconductor process evidence; not wire-bond
  telemetry and not an executed dataset in this repository.
- Sources: arXiv [2404.05183](https://arxiv.org/abs/2404.05183) and IEEE ICCE
  2025 DOI [10.1109/ICCE63647.2025.10930135](https://doi.org/10.1109/ICCE63647.2025.10930135).
- The ASE-provided drilling/AOI study reports 455 samples: 225 normal and four
  defect classes containing 92, 44, 50, and 44 samples.
- Boundary: these counts belong only to the drilling dataset. They must not be
  attributed to the embargoed ASE wire-bond thesis or treated as equipment
  telemetry.

### UTAC wafer-saw industrial practice

- Classification: `PUBLISHED_REAL_OSAT_STUDY`; target `WS-01`, corporate
  industrial-practice evidence.
- Source: [UTAC Sustainability Report 2023](https://utacgroup.com/wp-content/uploads/2025/04/UTAC_Sustainability_Report_2023.pdf).
- The report describes DISCO wafer saws, machine logs, FDC/data mining,
  predictive alerts, and maintenance.
- Boundary: no public telemetry was found. This is not executed evidence and
  cannot calibrate the WS relation.

### Final-test handler study

- Classification: strong real-semiconductor equipment evidence; OSAT setting
  is not asserted here.
- Source: DOI [10.1016/j.cie.2026.111872](https://doi.org/10.1016/j.cie.2026.111872).
- The study uses upstream test-handler motor signatures and downstream DUT
  electrical-test results for equipment fault detection/prognostics.
- Boundary: publication evidence only. No raw records or FT-01 current,
  position, velocity, motor, drive, control-mode, or phase semantics are present,
  so no physical equation is created.

## Public supporting datasets

### STMicroelectronics ST-AWFD

- Official source: [STMicroelectronics/ST-AWFD](https://github.com/STMicroelectronics/ST-AWFD).
- D1: 602,108 rows and 5,105 MaterialIDs. D2: 126,795 rows and 1,157
  MaterialIDs. Both are real semiconductor production data with normal/abnormal
  labels.
- Boundary: features are normalized and lack the physical names/units needed
  for Step01 mapping. The dataset therefore cannot validate a Step01 relation.

### TUHH DISCO DAD3350

- Source: DOI [10.15480/882.15763](https://doi.org/10.15480/882.15763).
- Open real-equipment dataset from fused-silica wafer dicing on a DISCO DAD3350
  at varying feed velocities; raw optical-profilometer measurements are public.
- Boundary: target-process/surface evidence, not machine-health validation or
  spindle telemetry.

### CHDL

- Source: [arXiv:2507.06738](https://arxiv.org/abs/2507.06738).
- Public temporal image evidence for semiconductor wafer dicing.
- Boundary: catalog only. Step01 adds no vision or deep-learning subsystem and
  makes no equipment-health claim from the images.

## Execution statement

`EXECUTED_REAL_OSAT_DATA`: **none**. The entries above generate no OSAT score,
health state, maintenance ticket, calibration, or evidence claim from
paper-only material.
