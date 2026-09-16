# External NASA Milling benchmark

OSAT Fleet Command 0.2.3 includes an optional, isolated parser and descriptive
analysis for the official NASA/UC Berkeley Milling Data Set. NASA describes the
data as milling experiments provided by the UC Berkeley BEST Lab with varying
operating conditions and measured flank wear.

This is an **EXTERNAL REAL-DATA BENCHMARK** using **NON-SEMICONDUCTOR MACHINING
DATA**. It is not OSAT data, real-plant validation, prospective validation,
production qualification, causal diagnosis, or evidence that Fleet Command
predicts semiconductor-equipment failures.

## Obtain and run it explicitly

Raw external data are not bundled and are never downloaded automatically.
Review the source and download the Milling archive from the official
[NASA Prognostics Data Repository](https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/)
or its [NASA Open Data record](https://data.nasa.gov/dataset/milling-wear). Keep
the artifact under ignored `benchmarks/_external/` or another approved local
directory.

```powershell
.venv\Scripts\python -m pip install -r requirements-benchmarks.txt
.venv\Scripts\python -m osat_edge.cli benchmark-nasa-milling --dataset benchmarks\_external\NASA_Milling.zip
```

Pass `--output path\report.json` only when a full per-run JSON report is wanted.
Without it, the command writes no report artifact and prints a concise summary.
Missing input exits cleanly with `NASA MILLING DATASET NOT FOUND`.

## Verified official structure and semantics

The supplied `Readme.pdf` documents a MATLAB `mill` struct array with fields
`case`, `run`, `VB`, `time`, `DOC`, `feed`, `material`, `smcAC`, `smcDC`,
`vib_table`, `vib_spindle`, `AE_table`, and `AE_spindle`. It identifies:

- `VB` as measured flank wear in mm, with measurements absent for some runs;
- `DOC` as depth of cut in mm;
- `feed` as mm/rev;
- material code 1 as cast iron and 2 as stainless steel J45;
- `smcAC` and `smcDC` as separate AC and DC spindle-motor-current signals;
- `vib_spindle` as the spindle vibration acquisition signal.

The README does not establish physical output units for the three analyzed
sample arrays, so the report does not invent amperes or acceleration units for
them. It reports a constant experiment setting of 200 m/min cutting speed,
corresponding to 826 rev/min, but the MATLAB structure contains no compatible
spindle-speed time series. Fleet Command therefore does not run its wafer-saw
current-versus-speed physics relation on this data.

## Descriptive method

For every run, the benchmark computes median, RMS, and scaled median absolute
deviation for `smcAC`, `smcDC`, and `vib_spindle`; AC and DC are never merged.
It reports the available wear association with Spearman rank correlation both
pooled and within each depth/feed/material group. This is descriptive
association, not a predictive model, probability, causal claim, health score,
or maintenance decision. No random split is used because no model is trained.

Operating condition is an explicit confounder: cutting depth, feed, material,
tool insert, and run progression can affect both signals and observed wear.
Pooled associations therefore cannot be read as isolated wear effects, and
even within-condition associations remain observational.

## Verified local result for 0.2.3

The official archive checked during release work had SHA-256
`bdba8d52ec1a1baab24c2be58480e6ac62508c8cc1f8219f47ebde8fc9ebc474`.
It contained 167 runs across 16 cases and eight depth/feed/material
combinations; 146 runs had finite `VB` values. The pooled Spearman association
with `VB` was 0.725 for AC-current RMS, 0.740 for DC-current RMS, and -0.530 for
spindle-vibration RMS. Within-condition AC-current RMS associations ranged
from 0.778 to 1.000, while spindle-vibration RMS associations ranged from
-0.888 to -0.339. These values are reproducibility observations for that exact
artifact, not universal effect estimates or OSAT validation.

The benchmark module imports no OSAT physics, exact-machine model, health,
maintenance, or UI component. It returns `DataOrigin.EXTERNAL_BENCHMARK` and
explicitly records that semiconductor data, OSAT data, plant validation, and
production qualification are false.
