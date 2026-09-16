"""Step 05: lightweight, real-only, machine-family risk scoring."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from ...pre_steps.pre01_common.pre01_common import DataOrigin, RuntimeMode
from ..step04_family_data.step04_family_data import FamilyDataset


@dataclass(frozen=True)
class FamilyModel:
    family: str
    origin: DataOrigin
    feature_names: tuple[str, ...]
    scaler_center: np.ndarray
    scaler_scale: np.ndarray
    coefficients: np.ndarray
    intercept: float

    def __post_init__(self) -> None:
        if not self.family.strip() or not self.feature_names:
            raise ValueError("Family and feature names are required")
        if len(self.feature_names) != len(set(self.feature_names)) or not all(
            name.strip() for name in self.feature_names
        ):
            raise ValueError("Family-model feature names must be nonempty and unique")
        width = len(self.feature_names)
        arrays = tuple(
            np.asarray(array, dtype=np.float64).copy()
            for array in (self.scaler_center, self.scaler_scale, self.coefficients)
        )
        if any(array.shape != (width,) for array in arrays):
            raise ValueError("Family model vector width does not match its feature schema")
        center, scale, coefficients = arrays
        if not all(bool(np.isfinite(array).all()) for array in arrays) or not np.isfinite(self.intercept):
            raise ValueError("Family model values must be finite")
        if not bool(np.all(scale > 0.0)):
            raise ValueError("Family-model scaler scale must be positive")
        for array in arrays:
            array.setflags(write=False)
        object.__setattr__(self, "scaler_center", center)
        object.__setattr__(self, "scaler_scale", scale)
        object.__setattr__(self, "coefficients", coefficients)


def _validate_machine_isolation(
    labels: np.ndarray,
    machine_ids: np.ndarray,
) -> None:
    """Ensure every held-out-machine training split retains both classes."""

    machines = tuple(dict.fromkeys(machine_ids.tolist()))
    for held_out in machines:
        train = machine_ids != held_out
        if len(np.unique(labels[train])) < 2:
            raise ValueError("Every held-out-machine training fold requires both classes")


def fit_family_model(
    dataset: FamilyDataset,
    *,
    minimum_machines: int = 3,
    minimum_independent_events: int = 3,
    minimum_positive_windows: int = 6,
) -> FamilyModel:
    if dataset.origin is not DataOrigin.REAL_OSAT:
        raise ValueError("Family-model training requires REAL_OSAT data")
    matrix, labels, machine_ids = dataset.training_arrays()
    machines = tuple(dict.fromkeys(machine_ids.tolist()))
    if len(machines) < minimum_machines:
        raise ValueError(f"At least {minimum_machines} same-family machines are required")
    if dataset.independent_event_count < minimum_independent_events:
        raise ValueError("Insufficient independent observed events")
    if int(np.sum(labels)) < minimum_positive_windows:
        raise ValueError("Insufficient positive windows")
    if len(np.unique(labels)) < 2:
        raise ValueError("Family data requires both event and non-event windows")
    _validate_machine_isolation(labels, machine_ids)
    scaler = StandardScaler().fit(matrix)
    estimator = LogisticRegression(
        C=0.5,
        class_weight="balanced",
        solver="liblinear",
        random_state=0,
    ).fit(scaler.transform(matrix), labels)
    return FamilyModel(
        family=dataset.family,
        origin=dataset.origin,
        feature_names=dataset.feature_names,
        scaler_center=np.asarray(scaler.mean_, dtype=np.float64),
        scaler_scale=np.asarray(scaler.scale_, dtype=np.float64),
        coefficients=np.asarray(estimator.coef_[0], dtype=np.float64),
        intercept=float(np.asarray(estimator.intercept_).reshape(-1)[0]),
    )


def score_family_model(
    model: FamilyModel,
    *,
    active_family: str,
    features: dict[str, float],
    runtime_mode: RuntimeMode,
) -> float:
    """Return an uncalibrated machine-wide risk_score."""

    if active_family != model.family:
        raise ValueError(
            f"Family model for {model.family} cannot score {active_family}"
        )
    if runtime_mode is not RuntimeMode.SIMULATION and model.origin is not DataOrigin.REAL_OSAT:
        raise ValueError("REAL_REPLAY/LIVE_EQUIPMENT reject synthetic family models")
    if any(name not in features for name in model.feature_names):
        raise ValueError("Family-model feature schema is unavailable")
    values = np.asarray([features[name] for name in model.feature_names], dtype=np.float64)
    if not bool(np.isfinite(values).all()):
        raise ValueError("Family-model inputs must be finite")
    standardized = (values - model.scaler_center) / model.scaler_scale
    logit = float(standardized @ model.coefficients + model.intercept)
    return float(1.0 / (1.0 + np.exp(-np.clip(logit, -40.0, 40.0))))
