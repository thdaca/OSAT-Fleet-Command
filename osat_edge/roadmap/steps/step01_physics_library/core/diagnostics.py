"""Deterministic residual diagnostics for Step01 research."""

from __future__ import annotations

import numpy as np

from .schema import ResidualDiagnostics


def _autocorrelation(values: np.ndarray, lag: int) -> float | None:
    if len(values) <= lag or float(np.std(values[:-lag])) == 0.0 or float(np.std(values[lag:])) == 0.0:
        return None
    result = float(np.corrcoef(values[:-lag], values[lag:])[0, 1])
    return result if np.isfinite(result) else None


def residual_diagnostics(
    residuals: np.ndarray,
    conditioning: np.ndarray | None = None,
    outside_envelope: np.ndarray | None = None,
) -> ResidualDiagnostics:
    """Deterministic residual structure checks; these are not release scores."""

    raw = np.asarray(residuals, dtype=float).reshape(-1)
    finite_mask = np.isfinite(raw)
    values = raw[finite_mask]
    finite_fraction = float(np.mean(finite_mask)) if len(raw) else 0.0
    outside_fraction = float(np.mean(np.asarray(outside_envelope, dtype=bool))) if outside_envelope is not None and len(outside_envelope) else 0.0
    if not len(values):
        nan = float("nan")
        return ResidualDiagnostics(0, finite_fraction, nan, nan, nan, None, None, None, outside_fraction)
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    split = len(values) // 2
    drift = float(np.median(values[split:]) - np.median(values[:split])) if split else 0.0
    slope: float | None = None
    if conditioning is not None:
        condition = np.asarray(conditioning, dtype=float).reshape(-1)
        if len(condition) == len(raw):
            x = condition[finite_mask]
            valid = np.isfinite(x)
            x, y = x[valid], values[valid]
            if len(x) >= 3 and float(np.ptp(x)) > 0.0:
                slope_value = float(np.polyfit(x, y, 1)[0])
                slope = slope_value if np.isfinite(slope_value) else None
    correlations = [value for lag in range(1, min(10, len(values) // 4) + 1) if (value := _autocorrelation(values, lag)) is not None]
    lag1 = _autocorrelation(values, 1)
    maximum = max((abs(value) for value in correlations), default=None)
    return ResidualDiagnostics(len(values), finite_fraction, median, mad, drift, slope, lag1, maximum, outside_fraction)

