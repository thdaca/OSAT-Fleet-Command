# WB-04 minimum de-identified data request

Request only the fields necessary to evaluate the research hypothesis:

- pseudonymous machine ID and model;
- timestamps and run/cycle boundaries;
- exact engineering units and acquisition/aggregation definitions;
- Bond Force;
- USG Current;
- USG Impedance, including the machine/OEM definition;
- Capillary Count;
- Z at Contact and Z at End of Bonding (and other supplied Z values only when
  their exact semantics are documented);
- pseudonymous recipe/context identifiers sufficient to separate regimes;
- alarm records;
- MES inspection and scrap labels;
- maintenance events, if available;
- independently adjudicated healthy/fault intervals, if available.

Do not request or accept customer or product identity. Device/lot/recipe names,
PPIDs, wafer maps, proprietary geometry, process windows, and calibration
constants outside the approved PHM boundary are unnecessary. Stable opaque
context identifiers are sufficient.

The request does not pre-map any field to a canonical channel. Data must remain
unexecuted until its source, approval, identity, units, semantics, and provenance
are verified. Requestable confidential data is not `EXECUTED_REAL_OSAT_DATA`.
