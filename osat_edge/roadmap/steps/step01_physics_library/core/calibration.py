"""Exact-machine Step01 calibration and held-out validation helpers."""

from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np

from .diagnostics import residual_diagnostics
from .schema import (
    AlignedSignals,
    ApplicabilityEnvelope,
    CalibrationReport,
    ParameterStabilityDiagnostics,
    ValidationDiagnostics,
)
from ..families import PHYSICS_RELATIONS
from ..families.wafer_saw import (
    INTERCEPT,
    MINIMUM_RUNTIME_SAMPLES,
    MINIMUM_SPINDLE_FIT_SAMPLES,
    RESIDUAL_SCALE,
    SLOPE,
    SPEED_HIGH,
    SPEED_LOW,
    SPEED_SPAN,
    _finite_pair,
    _fit_current_speed,
    _raw_spindle_residuals,
)


def _block_parameter_stability(signals: AlignedSignals, blocks: int = 3) -> ParameterStabilityDiagnostics:
    speed, current = _finite_pair(signals, "spindle_speed", "spindle_current")
    if blocks < 2 or len(speed) < blocks * MINIMUM_SPINDLE_FIT_SAMPLES:
        return ParameterStabilityDiagnostics(False, blocks, (), ("Insufficient samples for chronological block fits.",))
    fitted: list[Mapping[str, float]] = []
    for indices in np.array_split(np.arange(len(speed)), blocks):
        try:
            fitted.append(_fit_current_speed({"spindle_speed": speed[indices], "spindle_current": current[indices]}))
        except ValueError as exc:
            return ParameterStabilityDiagnostics(False, blocks, (), (f"Block calibration failed: {exc}",))
    relative_ranges: list[tuple[str, float]] = []
    for name in (SLOPE, INTERCEPT, RESIDUAL_SCALE):
        values = np.asarray([item[name] for item in fitted])
        denominator = max(abs(float(np.median(values))), 1e-12)
        relative_ranges.append((name, float(np.ptp(values)) / denominator))
    return ParameterStabilityDiagnostics(True, blocks, tuple(relative_ranges), ("Chronological deterministic blocks; no bootstrap inference.",))


def calibrate_relation(relation_id: str, signals: AlignedSignals, *, blocks: int = 3) -> CalibrationReport:
    relation = next((item for item in PHYSICS_RELATIONS if item.relation_id == relation_id), None)
    if relation is None or relation.fit is None:
        raise ValueError(f"No fitted runtime relation {relation_id!r}")
    parameters = dict(relation.fit(signals))
    residual, speed, outside = _raw_spindle_residuals(signals, parameters)
    diagnostics = residual_diagnostics(residual, speed, outside)
    stability = _block_parameter_stability(signals, blocks)
    blockers: list[str] = []
    if not stability.assessable:
        blockers.append("Parameter stability is not assessable across chronological blocks.")
    envelope = ApplicabilityEnvelope(
        (("spindle_speed", parameters[SPEED_LOW], parameters[SPEED_HIGH], "RPM"),),
        ("exact machine used for calibration", "unchanged controller/current semantics", "represented healthy cutting regimes"),
        ("Evaluation outside the speed range is refused, not extrapolated.", "Other operating variables remain unbounded until measured."),
    )
    return CalibrationReport(
        relation_id=relation_id,
        parameters=tuple(parameters.items()),
        sample_count=diagnostics.sample_count,
        excitation_summary=(("speed_low_rpm", parameters[SPEED_LOW]), ("speed_high_rpm", parameters[SPEED_HIGH]), ("speed_span_rpm", parameters[SPEED_SPAN])),
        applicability_envelope=envelope,
        calibration_diagnostics=diagnostics,
        parameter_stability=stability,
        blockers=tuple(blockers),
        valid=diagnostics.sample_count >= MINIMUM_RUNTIME_SAMPLES and stability.assessable,
    )


def validate_relation_calibration(
    relation_id: str,
    calibration_signals: AlignedSignals,
    validation_signals: AlignedSignals,
    *,
    calibration_run_ids: Sequence[str] | None = None,
    validation_run_ids: Sequence[str] | None = None,
) -> ValidationDiagnostics:
    """Fit calibration data and assess declared held-out run provenance."""

    report = calibrate_relation(relation_id, calibration_signals)
    parameters = dict(report.parameters)
    relation = next(item for item in PHYSICS_RELATIONS if item.relation_id == relation_id)
    shared = calibration_signals is validation_signals
    identical = True
    for channel in relation.required_channels:
        if channel in calibration_signals and channel in validation_signals:
            calibration_values = np.asarray(calibration_signals[channel])
            validation_values = np.asarray(validation_signals[channel])
            shared = shared or bool(np.shares_memory(calibration_values, validation_values))
            identical = identical and bool(
                np.array_equal(calibration_values, validation_values, equal_nan=True)
            )
        else:
            identical = False
    calibration_runs = {
        run_id.strip() for run_id in calibration_run_ids or () if run_id.strip()
    }
    validation_runs = {
        run_id.strip() for run_id in validation_run_ids or () if run_id.strip()
    }
    provenance_supplied = bool(calibration_runs) and bool(validation_runs)
    disjoint_runs = provenance_supplied and calibration_runs.isdisjoint(validation_runs)
    independent = not shared and not identical and disjoint_runs
    residual, speed, outside = _raw_spindle_residuals(validation_signals, parameters)
    diagnostics = residual_diagnostics(residual, speed, outside)
    blockers = list(report.blockers)
    if shared:
        blockers.append("Validation data share identity or memory with calibration data.")
    elif identical:
        blockers.append("Validation data exactly copy the calibration observations.")
    if not provenance_supplied:
        blockers.append("Independent validation run provenance was not supplied.")
    elif not disjoint_runs:
        blockers.append("Calibration and validation run IDs must be disjoint.")
    if diagnostics.sample_count < MINIMUM_RUNTIME_SAMPLES:
        blockers.append("Too few held-out observations fall inside the applicability envelope.")
    if independent:
        note = "Distinct observations with explicit nonempty disjoint run IDs were supplied."
    else:
        note = "Independent experimental validation was not established."
    return ValidationDiagnostics(
        relation_id, report, diagnostics, independent, note,
        tuple(blockers),
    )

