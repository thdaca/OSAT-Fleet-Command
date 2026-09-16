"""Explicit linearized uncertainty propagation for Step01."""

from __future__ import annotations

import numpy as np


def propagate_linearized_uncertainty(jacobian: np.ndarray, covariance: np.ndarray) -> float:
    """Return sqrt(J Σ Jᵀ) for one scalar output; no distributions are invented."""

    j = np.asarray(jacobian, dtype=float).reshape(1, -1)
    sigma = np.asarray(covariance, dtype=float)
    if sigma.shape != (j.shape[1], j.shape[1]):
        raise ValueError("Covariance dimensions must match the Jacobian")
    if not bool(np.all(np.isfinite(j))) or not bool(np.all(np.isfinite(sigma))):
        raise ValueError("Jacobian and covariance must be finite")
    if not bool(np.allclose(sigma, sigma.T, rtol=1e-10, atol=1e-12)):
        raise ValueError("Covariance must be symmetric")
    eigenvalues = np.linalg.eigvalsh(sigma)
    if float(np.min(eigenvalues)) < -1e-12:
        raise ValueError("Covariance must be positive semidefinite")
    variance = float((j @ sigma @ j.T).item())
    if variance < -1e-12:
        raise ValueError("Propagated variance cannot be negative")
    return float(np.sqrt(max(variance, 0.0)))

