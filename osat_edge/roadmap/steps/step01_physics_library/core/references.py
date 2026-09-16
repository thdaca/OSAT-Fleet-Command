"""Bibliography metadata for Step01 engineering evidence."""

from __future__ import annotations

from .schema import ReferenceType, ResearchReference


def _reference(
    key: str,
    citation: str,
    identifier: str,
    reference_type: ReferenceType,
    year: int | None,
    supports: str,
    limits: str,
) -> ResearchReference:
    return ResearchReference(key, citation, identifier, reference_type, year, supports, limits)


ISO_DIAGNOSTICS = _reference(
    "iso_13379_1_2025", "ISO 13379-1:2025, Condition monitoring and diagnostics of machine systems — Data interpretation and diagnostics techniques — Part 1: General guidelines.", "ISO 13379-1:2025", ReferenceType.STANDARD, 2025,
    "Application-specific diagnostic selection and stated operating context.", "A general process standard; it validates no OSAT residual.")
ISO_CONDITION_MONITORING = _reference(
    "iso_17359_2018", "ISO 17359:2018, Condition monitoring and diagnostics of machines — General guidelines, 3rd ed.", "ISO 17359:2018", ReferenceType.STANDARD, 2018,
    "Condition-monitoring programs should define technique, accuracy, operating conditions, acquisition rate, and measurement location.", "General guidance, not equipment-specific thresholds.")
ISO_MEASUREMENT_MANAGEMENT = _reference(
    "iso_10012_2026", "ISO 10012:2026, Quality management — Requirements for measurement management systems, 2nd ed.", "ISO 10012:2026", ReferenceType.STANDARD, 2026,
    "Management of measurement processes and metrological confirmation.", "Conformance is not claimed by this project.")
ISO_VIBRATION_CALIBRATION = _reference(
    "iso_16063_21_2003", "ISO 16063-21:2003, Methods for calibration of vibration and shock transducers — Part 21: Vibration calibration by comparison to a reference transducer.", "ISO 16063-21:2003", ReferenceType.STANDARD, 2003,
    "Comparison calibration of vibration transducers.", "Does not supply machine-health alarm limits.")
ISO_VIBRATION_SCOPE = _reference(
    "iso_20816_3_2022", "ISO 20816-3:2022, Mechanical vibration — Measurement and evaluation of machine vibration — Part 3: Industrial machinery above 15 kW and 120 to 30 000 r/min.", "ISO 20816-3:2022", ReferenceType.STANDARD, 2022,
    "An explicit example of machinery-scope limits for vibration criteria.", "Its >15 kW and <=30 000 r/min scope does not fit the cited 1.8 kW, 60 000 r/min dicing spindle; no limits are imported.")
JCGM_UNCERTAINTY = _reference(
    "jcgm_100_2008", "JCGM 100:2008, Evaluation of measurement data — Guide to the expression of uncertainty in measurement.", "10.59161/JCGM100-2008E", ReferenceType.METROLOGY_GUIDE, 2008,
    "Measurement-model uncertainty budgets and linearized propagation.", "An uncertainty budget needs quantified input distributions/covariances; this code has none for plant sensors.")
JCGM_VIM = _reference(
    "jcgm_200_2012", "JCGM 200:2012, International vocabulary of metrology — Basic and general concepts and associated terms, 3rd ed.", "10.59161/JCGM200-2012", ReferenceType.METROLOGY_GUIDE, 2012,
    "Vocabulary for measurand, calibration, traceability, and uncertainty.", "Terminology does not establish traceability for repository telemetry.")
JCGM_MONTE_CARLO = _reference(
    "jcgm_101_2008", "JCGM 101:2008, Supplement 1 to the GUM — Propagation of distributions using a Monte Carlo method.", "10.59161/JCGM101-2008", ReferenceType.METROLOGY_GUIDE, 2008,
    "Propagation of supplied probability distributions through a measurement model.", "No distributions are available here and no runtime Monte Carlo is implemented.")
NASA_MODEL_STANDARD = _reference(
    "nasa_std_7009b", "NASA-STD-7009B, Standard for Models and Simulations, 2024.", "NASA-STD-7009B", ReferenceType.STANDARD, 2024,
    "Model lifecycle, intended use, acceptance criteria, and credibility-product practices.", "This student project does not claim NASA-standard compliance.")
NASA_MODEL_HANDBOOK = _reference(
    "nasa_hdbk_7009b", "NASA-HDBK-7009B, NASA Handbook for Models and Simulations: An Implementation Guide for NASA-STD-7009B, 2026.", "NASA-HDBK-7009B", ReferenceType.GOVERNMENT_TECHNICAL, 2026,
    "Guidance for communicating model credibility and limitations.", "General model guidance, not evidence for an OSAT relation.")
ASME_UNCERTAINTY = _reference(
    "asme_vvuq_10_2_2021", "ASME VVUQ 10.2-2021, The Role of Uncertainty Quantification in Verification and Validation of Computational Solid Mechanics Models.", "ASME VVUQ 10.2-2021", ReferenceType.STANDARD, 2021,
    "Separation of model-form, numerical, input, experimental, and validation uncertainty.", "Computational-solid-mechanics scope; used only for general V&V/UQ discipline.")
NIST_PHM = _reference(
    "nist_phm4sm", "NIST, Prognostics and Health Management for Reliable Operations in Smart Manufacturing (PHM4SM), project page updated 2025.", "NIST PHM4SM", ReferenceType.GOVERNMENT_TECHNICAL, 2025,
    "PHM verification and validation needs laboratory testbeds, metrics, reference data, and pilot tests.", "NIST work targets manufacturing workcells; it does not validate these OSAT relations.")
NIST_ROADMAP = _reference(
    "nist_ams_100_2", "J. Pellegrino et al., Measurement Science Roadmap for Prognostics and Health Management for Smart Manufacturing Systems, NIST AMS 100-2, 2016.", "10.6028/NIST.AMS.100-2", ReferenceType.GOVERNMENT_TECHNICAL, 2016,
    "Measurement science, PHM performance assessment, V&V, uncertainty, and infrastructure gaps.", "A roadmap, not an equipment validation study.")
KHAN_REVIEW = _reference(
    "khan_2024_physics_learning", "S. Khan, T. Yairi, S. Tsutsumi, and S. Nakasuka, A review of physics-based learning for system health management, Annual Reviews in Control 57 (2024) 100932.", "10.1016/j.arcontrol.2024.100932", ReferenceType.PEER_REVIEWED_REVIEW, 2024,
    "Taxonomy and research state of physics-based learning for health management.", "Broad system-health review; not evidence for a specific OSAT sensor relation.")
DENG_REVIEW = _reference(
    "deng_2023_piml_phm", "W. Deng et al., Physics-informed machine learning in prognostics and health management: State of the art and challenges, Applied Mathematical Modelling 124 (2023) 325–352.", "10.1016/j.apm.2023.07.011", ReferenceType.PEER_REVIEWED_REVIEW, 2023,
    "PIML-PHM taxonomy, opportunities, and limitations.", "Review-level context, not calibration evidence.")
BRAUN_PREPRINT = _reference(
    "braun_2026_piml_phm", "C. Braun, J. Raible, and M. F. Huber, Physics-Informed Machine Learning in Prognostics and Health Management: A Systematic Literature Review, arXiv preprint, submitted 10 August 2026.", "arXiv:2608.10047", ReferenceType.PREPRINT, 2026,
    "Provisional systematic-review context for PIML-PHM evidence gaps.", "Final journal publication was not verified on the review date; preprint only and no relation validation.")
KENNEDY_OHAGAN = _reference(
    "kennedy_ohagan_2001", "M. C. Kennedy and A. O'Hagan, Bayesian calibration of computer models, JRSS B 63(3) (2001) 425–464.", "10.1111/1467-9868.00294", ReferenceType.PEER_REVIEWED_PRIMARY, 2001,
    "Calibration should account for parameter uncertainty and model inadequacy.", "Its Bayesian method is not implemented here; cited for the discrepancy distinction.")
BRYNJARSDOTTIR_OHAGAN = _reference(
    "brynjarsdottir_ohagan_2014", "J. Brynjarsdóttir and A. O'Hagan, Learning about physical parameters: the importance of model discrepancy, Inverse Problems 30 (2014) 114007.", "10.1088/0266-5611/30/11/114007", ReferenceType.PEER_REVIEWED_PRIMARY, 2014,
    "Ignoring model discrepancy can bias and overstate confidence in calibrated parameters.", "Illustrative calibration study; it supplies no discrepancy magnitude for this project.")
RAUE_IDENTIFIABILITY = _reference(
    "raue_2009_identifiability", "A. Raue et al., Structural and practical identifiability analysis of partially observed dynamical models by exploiting the profile likelihood, Bioinformatics 25(15) (2009) 1923–1929.", "10.1093/bioinformatics/btp358", ReferenceType.PEER_REVIEWED_PRIMARY, 2009,
    "Practical identifiability depends on observations and excitation, not only equation form.", "Dynamical biological examples; profile likelihood is not implemented here.")
FRANK_DING_RESIDUAL = _reference(
    "frank_ding_1997", "P. M. Frank and X. Ding, Survey of robust residual generation and evaluation methods in observer-based fault detection systems, Journal of Process Control 7(6) (1997) 403–424.", "10.1016/S0959-1524(97)00016-4", ReferenceType.PEER_REVIEWED_REVIEW, 1997,
    "Residual evaluation must consider robustness to disturbances and model uncertainty.", "Observer-based dynamic systems differ from this simple static residual.")
DICING_MONITOR_PATENT = _reference(
    "dicing_monitor_patent", "I. Weisshaus and O. Y. Licht, Monitoring system for dicing saws, US patent, 2001.", "US6168500B1", ReferenceType.PATENT, 2001,
    "One dicing-saw implementation used spindle feedback current as a cutting-load signal while holding speed.", "A patent is not validation, does not establish universality, and does not prove fault specificity.")
DICING_DYNAMICS = _reference(
    "li_2026_dicing_dynamics", "J. Li et al., Vibration–force coupled dynamics and fracture evolution in wafer dicing, International Journal of Mechanical Sciences 319 (2026) 111581.", "10.1016/j.ijmecsci.2026.111581", ReferenceType.PEER_REVIEWED_PRIMARY, 2026,
    "Dicing force, vibration, fracture, and clogging dynamics are coupled.", "Published dicing study conditions are not automatically transferable to the demo station.")
DISCO_PRODUCT_LINE = _reference(
    "disco_product_line_2024", "DISCO Corporation, Product Lineup catalog, 2024.", "DISCO product_lineup.pdf", ReferenceType.OEM_TECHNICAL, 2024,
    "Public dicing-saw specifications include spindle examples at 1.8 kW and 60 000 min⁻¹.", "Product examples do not identify the simulated WS-01 hardware or its telemetry semantics.")
MAXON_CONSTANTS = _reference(
    "maxon_motor_constants", "maxon, Motor constants / Motor data and operating ranges, technical guidance.", "maxon motor constants", ReferenceType.OEM_TECHNICAL, 2024,
    "Torque constant relates motor current to produced torque under motor-model assumptions.", "Does not establish the controller's reported-current semantics or spindle losses.")
KEITHLEY_LOW_LEVEL = _reference(
    "keithley_low_level_7", "Keithley Instruments, Low Level Measurements Handbook, 7th ed.", "Keithley Low Level Measurements Handbook, 7th ed.", ReferenceType.MANUFACTURER_APPLICATION_NOTE, 2016,
    "Four-wire sensing, offset compensation, current reversal, settling, and dry-circuit practices for low/contact resistance.", "General metrology guidance; current repository channel names do not prove these practices.")
NI_SOCKET_GUIDANCE = _reference(
    "ni_smu_ic_sockets", "National Instruments, Best Practice for Using NI SMUs to Test IC in Sockets, updated 2025.", "NI SMU IC socket best practice", ReferenceType.MANUFACTURER_APPLICATION_NOTE, 2025,
    "Socket debris, wear, and intermittent connections matter to test connectivity.", "Does not prove this project's voltage channel isolates contact resistance.")
KEYSIGHT_LOW_RESISTANCE = _reference(
    "keysight_low_resistance", "Keysight Technologies, Precise Low Resistance Measurements Using the B2961B and 34420A, application note.", "Keysight 3120-1555", ReferenceType.MANUFACTURER_APPLICATION_NOTE, None,
    "Low-resistance measurement needs suitable current, synchronized voltage, offset control, and appropriate topology.", "Application setup is not evidence that repository telemetry follows it.")
LIU_WAFER_PROBE = _reference(
    "liu_2007_wafer_probe_contact", "D. S. Liu, M. K. Shih, and W. H. Huang, Measurement and analysis of contact resistance in wafer probe testing, Microelectronics Reliability 47(7) (2007) 1086–1094.", "10.1016/j.microrel.2006.07.091", ReferenceType.PEER_REVIEWED_PRIMARY, 2007,
    "Probe contact resistance is affected by contact condition and contamination.", "Wafer-probe contacts are not final-test sockets; no direct transfer claim is made.")
KEYENCE_POWER_MONITOR = _reference(
    "keyence_laser_power_monitor", "KEYENCE America, Laser marking resources: built-in thermopile power monitoring for detecting output-power drops.", "KEYENCE laser marking resource", ReferenceType.OEM_TECHNICAL, 2026,
    "Some commercial laser markers directly monitor optical output power for maintenance.", "Vendor-specific capability; it does not define this repository's channel or a universal degradation model.")
TRUMPF_CONDITION_MONITORING = _reference(
    "trumpf_laser_monitoring", "TRUMPF, Condition Monitoring for lasers and laser systems, service description.", "TRUMPF Condition Monitoring", ReferenceType.OEM_TECHNICAL, 2026,
    "Commercial laser condition monitoring uses equipment-specific service data and algorithms.", "Marketing/service description without an open transferable relation.")
WIRE_BOND_IMPEDANCE = _reference(
    "feng_2011_wire_bond", "W. Feng et al., Wire bonding quality monitoring via refining process of electrical signal from ultrasonic generator, MSSP 25(3) (2011) 884–900.", "10.1016/j.ymssp.2010.09.010", ReferenceType.PEER_REVIEWED_PRIMARY, 2011,
    "Wire-bond electrical monitoring used generator voltage/current and harmonic/phase information.", "Current plus low-rate frequency shift alone is insufficient to reproduce the method.")
WIRE_BOND_PIEZO = _reference(
    "or_1998_wire_bond", "S. W. Or et al., Ultrasonic wire-bond quality monitoring using piezoelectric sensor, Sensors and Actuators A 65(1) (1998) 69–75.", "10.1016/S0924-4247(97)01638-5", ReferenceType.PEER_REVIEWED_PRIMARY, 1998,
    "Dedicated PZT sensing captured dynamic wire-bond vibration behavior.", "Requires a dedicated dynamic sensor path absent from current telemetry.")
MOLDING_MONITOR = _reference(
    "kahle_2016_transfer_molding", "R. Kahle et al., In-situ measuring module for transfer molding process monitoring, IMAPS Proceedings (2016).", "10.4071/isom-2016-THA43", ReferenceType.PEER_REVIEWED_PRIMARY, 2016,
    "Transfer-mold research measures cavity pressure, material/tool temperature, and cure-related information.", "Experimental packaging work does not validate a clamp-pressure residual.")
MOLDING_PROCESS = _reference(
    "kaya_2019_transfer_molding", "B. Kaya et al., Process Optimization and Implementation of Online Monitoring Process in Transfer Molding for Electronic Packaging, JMEP (2019).", "10.4071/IMAPS.954402", ReferenceType.PEER_REVIEWED_PRIMARY, 2019,
    "Transfer molding depends on pressure, temperature, transfer conditions, material state, and cure behavior.", "Does not yield a generic equipment-health ratio from present channels.")
LASER_OUTPUT_MODEL = _reference(
    "borras_2019_laser_output", "R. Borràs et al., Laser diodes optical output power model, Measurement 133 (2019) 56–67.", "10.1016/j.measurement.2018.10.007", ReferenceType.PEER_REVIEWED_PRIMARY, 2019,
    "Compatible laser-diode output depends on drive, threshold/slope efficiency, and temperature.", "Cannot be transferred to an unknown fiber, solid-state, UV, pulsed, or closed-loop marker.")
LEYBOLD_LEAK = _reference(
    "leybold_pressure_rise", "Leybold, Fundamentals of Leak Detection: pressure-rise and pressure-drop tests.", "Leybold Fundamentals of Leak Detection", ReferenceType.OEM_TECHNICAL, None,
    "Pressure-rise leak-rate inference requires a known isolated volume and pressure change over time.", "Vacuum value during operation cannot by itself identify a leak.")
BRANCA_WEB = _reference(
    "branca_2013_web_tension", "C. Branca, P. R. Pagilla, and K. N. Reid, Governing equations for web tension and web velocity in the presence of nonideal rollers, ASME JDSMC 135(1) (2013) 011018.", "10.1115/1.4007974", ReferenceType.PEER_REVIEWED_PRIMARY, 2013,
    "Web tension/velocity dynamics depend on roller mechanics and nonideal effects.", "Not specific to wafer-mount tape handling and requires machine parameters absent here.")

INFINEON_TAPE_TENSION = _reference(
    "infineon_dicing_tape_tension",
    "W. Leitgeb, D. Brunner, and L. Ferlan, Method and device for monitoring a dicing tape tension, Infineon Technologies AG.",
    "EP3705862B1 / US20200286795A1",
    ReferenceType.PATENT,
    2020,
    "Wafer-mounter tape tension can be monitored per tape; tape maker/type/properties, roll changes, stretching, rollers, lamination, and frame deformation affect the result.",
    "Patent disclosure, not an independent validation study; it does not identify roller motor current as tension.",
)
DISCO_DAD3660 = _reference(
    "disco_dad3660",
    "DISCO Corporation, DAD3660 Automatic Dicing Saw product information.",
    "https://www.disco.co.jp/jp/products/dicer/dad3660.html",
    ReferenceType.OEM_TECHNICAL,
    2026,
    "The DAD3660 supports package singulation and exposes spindle-current monitoring as a condition-monitor function.",
    "Product capability does not define current acquisition semantics, prove fault specificity, or identify WS-01/SG-01 hardware.",
)
BESI_DIE_BONDER = _reference(
    "besi_9800_tc_next",
    "Besi, 9800 TC next product information, next-generation die attach for chiplet and interposer packages.",
    "https://www.besi.com/products-technology/product-details/product/9800-tc-next/",
    ReferenceType.OEM_TECHNICAL,
    2026,
    "A modern die bonder specifies bond-force accuracy, bond-head Z control, bond-head thermal control, bond traces, and inline process monitoring.",
    "Vendor/model-specific capability; it does not establish DA-01 channels, units, sampling, or health meaning.",
)
PTI_WIRE_BOND = _reference(
    "pti_wire_bond_2026",
    "C. T. Wu, S. H. Li, and C. S. Tsou, Integrating FDC and Machine Learning for Enhanced Anomaly Detection in WB Bonding Joint Quality, Computer Modeling in Engineering & Sciences 88(1) (2026) 96.",
    "10.32604/cmc.2026.078762",
    ReferenceType.PEER_REVIEWED_PRIMARY,
    2026,
    "A real Powertech OSAT wire-bond study reports the named production-machine fields and production inspection feedback.",
    "Company-confidential data are requestable but not public; field names omit engineering units and do not make machine-computed USG Impedance a derived electrical impedance.",
)
BESI_FICO_MOLDING = _reference(
    "besi_fico_molding_line",
    "Besi, Fico Molding Line product information.",
    "https://www.besi.com/products-technology/product-details/product/fico-molding-line/",
    ReferenceType.OEM_TECHNICAL,
    2026,
    "Semiconductor transfer-molding equipment exposes dynamic/active clamp-force control, dynamic transfer-pressure control, multi-zone temperature control, and cavity vacuum.",
    "Vendor/model-specific capabilities do not define MO-01 telemetry semantics or validate a health residual.",
)
GALLANT_TRIM_FORM = _reference(
    "gallant_trim_form",
    "Gallant Micro Machining Co., SP Series trim/form equipment product information.",
    "https://www.gmmcorp.com.tw/en/trim-form",
    ReferenceType.OEM_TECHNICAL,
    2026,
    "Semiconductor trim/form equipment is offered with an electric cam servo and stated tonnage capability.",
    "A product specification does not expose motor/control semantics or map drive current to punch force.",
)
TAIJIN_TRIM_FORM = _reference(
    "taijin_trim_form",
    "Guangdong Taijin Semiconductor Technology, Auto Trim/Form System product information.",
    "https://www.dgtj168.com/en/sys-pd/1.html",
    ReferenceType.OEM_TECHNICAL,
    2026,
    "A semiconductor trim/form system is described with servo-motor punch capability of 3-5 ton and package-specific tooling scope.",
    "Vendor specification only; it does not establish TF-01 drive feedback, force metrology, or tooling-health sensitivity.",
)
FINAL_TEST_HANDLER = _reference(
    "roy_2026_final_test_handler",
    "L. A. A. Roy, J. S. B. Beh, C. K. Yeo, and S. Regunathan, Process-aware graph-temporal framework for equipment prognostics with multimodal data at semiconductor final test, Computers & Industrial Engineering 214 (2026) 111872.",
    "10.1016/j.cie.2026.111872",
    ReferenceType.PEER_REVIEWED_PRIMARY,
    2026,
    "A real semiconductor final-test study combines upstream test-handler motor signatures with downstream DUT electrical-test readouts for equipment fault detection/prognostics.",
    "The publication is strong domain evidence but supplies no transferable physical equation or FT-01 measurement semantics.",
)
ST_AWFD = _reference(
    "st_awfd",
    "STMicroelectronics, ST Dataset for Automatic Wafer Fault Detection (ST-AWFD), official GitHub repository.",
    "https://github.com/STMicroelectronics/ST-AWFD",
    ReferenceType.DATASET_REPOSITORY,
    2021,
    "Real semiconductor production sequences with normal/abnormal labels: D1 has 602108 rows/5105 MaterialIDs and D2 has 126795 rows/1157 MaterialIDs.",
    "Feature columns are normalized and lack physical names/units, so they cannot map to Step01 physical variables.",
)
TUHH_DAD3350 = _reference(
    "tuhh_dad3350_2026",
    "L. Rennpferdt, S. Bohne, and H. K. Trieu, Optical Profilometer Dataset for Diced Surfaces Obtained with Wafer Dicing Machine at Varying Feed Velocities.",
    "10.15480/882.15763",
    ReferenceType.DATASET_REPOSITORY,
    2026,
    "Open raw optical-profilometer measurements from fused-silica wafers diced on a DISCO DAD3350 at varying feed velocities.",
    "Target-process/surface evidence, not machine-health validation or spindle telemetry.",
)
CHDL = _reference(
    "chdl_2025",
    "X. Xie et al., DIFFUMA: High-Fidelity Spatio-Temporal Video Prediction via Dual-Path Mamba and Diffusion Enhancement; introduces the Chip Dicing Lane Dataset.",
    "arXiv:2507.06738",
    ReferenceType.PREPRINT,
    2025,
    "Public temporal image evidence from semiconductor wafer dicing.",
    "Process imagery only; no vision/deep-learning subsystem is added and it does not validate equipment health.",
)
AMKOR_ATEP = _reference(
    "amkor_atep_2022",
    "T. N. da C. Fernandes, Implementação de manutenção preditiva numa indústria de semicondutores, ISEP master's dissertation.",
    "hdl:10400.22/20698",
    ReferenceType.ACADEMIC_THESIS,
    2022,
    "Published real-OSAT monitoring of ATEP/Amkor Portugal liquid-ring vacuum pumps, including an observed post-deployment failure and two-year maintenance history.",
    "Auxiliary, noncanonical equipment; the public artifact is a thesis, not raw executable time-series data.",
)
ASE_WIRE_BOND_AOI = _reference(
    "ase_wire_bond_aoi_2025",
    "C.-C. Hsu, AOI-Based Defect Detection in the Wire Bonding Process, National Sun Yat-sen University thesis record.",
    "etd-0609125-111038",
    ReferenceType.ACADEMIC_THESIS,
    2025,
    "Genuine ASE-provided wire-bond process/inspection evidence with 455 labeled samples.",
    "Process/AOI evidence only; no public raw download or equipment-health telemetry was identified.",
)
UTAC_WAFER_SAW = _reference(
    "utac_wafer_saw_2023",
    "UTAC Group, Sustainability Report 2023.",
    "https://utacgroup.com/wp-content/uploads/2025/04/UTAC_Sustainability_Report_2023.pdf",
    ReferenceType.CORPORATE_REPORT,
    2023,
    "Real-OSAT industrial-practice evidence describing DISCO wafer saws, machine logs, FDC/data mining, predictive alerts, and maintenance.",
    "Corporate practice evidence; no public telemetry or executable dataset is supplied.",
)


RESEARCH_REFERENCES: tuple[ResearchReference, ...] = (
    ISO_DIAGNOSTICS, ISO_CONDITION_MONITORING, ISO_MEASUREMENT_MANAGEMENT,
    ISO_VIBRATION_CALIBRATION, ISO_VIBRATION_SCOPE, JCGM_UNCERTAINTY,
    JCGM_VIM, JCGM_MONTE_CARLO, NASA_MODEL_STANDARD, NASA_MODEL_HANDBOOK,
    ASME_UNCERTAINTY, NIST_PHM, NIST_ROADMAP, KHAN_REVIEW, DENG_REVIEW,
    BRAUN_PREPRINT,
    KENNEDY_OHAGAN, BRYNJARSDOTTIR_OHAGAN, RAUE_IDENTIFIABILITY,
    FRANK_DING_RESIDUAL, DICING_MONITOR_PATENT, DICING_DYNAMICS,
    DISCO_PRODUCT_LINE, MAXON_CONSTANTS, KEITHLEY_LOW_LEVEL,
    NI_SOCKET_GUIDANCE, KEYSIGHT_LOW_RESISTANCE,
    LIU_WAFER_PROBE, KEYENCE_POWER_MONITOR, TRUMPF_CONDITION_MONITORING,
    WIRE_BOND_IMPEDANCE, WIRE_BOND_PIEZO, MOLDING_MONITOR,
    MOLDING_PROCESS, LASER_OUTPUT_MODEL, LEYBOLD_LEAK, BRANCA_WEB,
    INFINEON_TAPE_TENSION, DISCO_DAD3660, BESI_DIE_BONDER,
    PTI_WIRE_BOND, BESI_FICO_MOLDING, GALLANT_TRIM_FORM,
    TAIJIN_TRIM_FORM, FINAL_TEST_HANDLER, ST_AWFD, TUHH_DAD3350,
    CHDL, AMKOR_ATEP, ASE_WIRE_BOND_AOI, UTAC_WAFER_SAW,
)
