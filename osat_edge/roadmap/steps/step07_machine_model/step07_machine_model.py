"""Step 07: robust healthy model for one exact installed machine."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

import numpy as np

from ...pre_steps.pre01_common.pre01_common import DataOrigin, EquipmentState, MachineIdentity, RuntimeMode
from ..step02_physical_features.step02_physical_features import FeatureSet
from ..step06_machine_history.step06_machine_history import MachineHistory


@dataclass(frozen=True)
class ContextModel:
    equipment_state: EquipmentState
    feature_names: tuple[str, ...]
    subsystems: tuple[str, ...]
    kinds: tuple[str, ...]
    center: np.ndarray
    scale: np.ndarray

    def __post_init__(self) -> None:
        width = len(self.feature_names)
        if (
            width == 0
            or len(self.subsystems) != width
            or len(self.kinds) != width
            or len(set(self.feature_names)) != width
            or not all(name.strip() for name in self.feature_names)
        ):
            raise ValueError("Context-model metadata must have one unique entry per feature")
        center = np.asarray(self.center, dtype=np.float64).copy()
        scale = np.asarray(self.scale, dtype=np.float64).copy()
        if center.shape != (width,) or scale.shape != (width,):
            raise ValueError("Context-model arrays must match the feature width")
        if not bool(np.isfinite(center).all()) or not bool(np.isfinite(scale).all()):
            raise ValueError("Context-model center and scale must be finite")
        if not bool(np.all(scale > 0.0)):
            raise ValueError("Context-model scale must be positive")
        center.setflags(write=False)
        scale.setflags(write=False)
        object.__setattr__(self, "center", center)
        object.__setattr__(self, "scale", scale)


@dataclass(frozen=True)
class MachineModel:
    machine: MachineIdentity
    origin: DataOrigin
    contexts: Mapping[EquipmentState, ContextModel]
    physics_parameters: Mapping[str, Mapping[str, float]]

    def __post_init__(self) -> None:
        if not self.contexts:
            raise ValueError("Machine model requires at least one equipment-state context")
        if any(key is not context.equipment_state for key, context in self.contexts.items()):
            raise ValueError("Machine-model context keys must match their equipment states")
        if any(
            not np.isfinite(value)
            for parameters in self.physics_parameters.values()
            for value in parameters.values()
        ):
            raise ValueError("Machine-model physics parameters must be finite")
        object.__setattr__(self, "contexts", MappingProxyType(dict(self.contexts)))
        object.__setattr__(
            self,
            "physics_parameters",
            MappingProxyType(
                {
                    relation: MappingProxyType(dict(parameters))
                    for relation, parameters in self.physics_parameters.items()
                }
            ),
        )


@dataclass(frozen=True)
class FeatureDeviation:
    feature: str
    subsystem: str
    kind: str
    value: float
    healthy_center: float
    z_score: float
    score: float


@dataclass(frozen=True)
class MachineModelResult:
    available: bool
    deviations: tuple[FeatureDeviation, ...]
    reason: str | None = None


def fit_machine_model(
    history: MachineHistory,
    *,
    physics_parameters: Mapping[str, Mapping[str, float]] | None = None,
    minimum_rows_per_state: int = 12,
) -> MachineModel:
    healthy = history.healthy_feature_sets()
    if not healthy:
        raise ValueError("No feature windows fall fully inside confirmed healthy intervals")
    grouped: dict[EquipmentState, list[FeatureSet]] = {}
    for feature_set in healthy:
        grouped.setdefault(feature_set.equipment_state, []).append(feature_set)
    contexts: dict[EquipmentState, ContextModel] = {}
    for state, rows in grouped.items():
        if len(rows) < minimum_rows_per_state:
            continue
        schema = set(rows[0].by_name)
        for row in rows[1:]:
            schema.intersection_update(row.by_name)
        names = tuple(name for name in rows[0].by_name if name in schema)
        if not names:
            continue
        matrix = np.asarray(
            [[row.by_name[name].value for name in names] for row in rows],
            dtype=np.float64,
        )
        if not np.isfinite(matrix).all():
            raise ValueError("Healthy model features must be finite")
        center = np.median(matrix, axis=0)
        mad = 1.4826 * np.median(np.abs(matrix - center), axis=0)
        standard = np.std(matrix, axis=0)
        floor = np.maximum(np.abs(center) * 1e-2, 1e-4)
        scale = np.where(mad > floor, mad, np.where(standard > floor, standard, floor))
        first = rows[0].by_name
        contexts[state] = ContextModel(
            equipment_state=state,
            feature_names=names,
            subsystems=tuple(first[name].subsystem for name in names),
            kinds=tuple(first[name].kind for name in names),
            center=np.asarray(center, dtype=np.float64),
            scale=np.asarray(scale, dtype=np.float64),
        )
    if not contexts:
        raise ValueError("No equipment state has enough confirmed healthy feature windows")
    return MachineModel(
        machine=history.machine,
        origin=history.origin,
        contexts=contexts,
        physics_parameters=dict(physics_parameters or {}),
    )


def validate_machine_model(
    model: MachineModel,
    active_machine: MachineIdentity,
    runtime_mode: RuntimeMode,
) -> None:
    if model.machine.machine_id != active_machine.machine_id:
        raise ValueError(
            f"Machine model for {model.machine.machine_id} cannot score {active_machine.machine_id}"
        )
    if model.machine.family != active_machine.family:
        raise ValueError(
            f"Machine model family {model.machine.family} cannot score {active_machine.family}"
        )
    if model.machine.station_id != active_machine.station_id:
        raise ValueError(
            f"Machine model station {model.machine.station_id} cannot score {active_machine.station_id}"
        )
    if runtime_mode is not RuntimeMode.SIMULATION and model.origin is not DataOrigin.REAL_OSAT:
        raise ValueError("REAL_REPLAY/LIVE_EQUIPMENT reject synthetic exact-machine models")


def evaluate_machine_model(
    model: MachineModel,
    active_machine: MachineIdentity,
    feature_set: FeatureSet,
    *,
    runtime_mode: RuntimeMode,
) -> MachineModelResult:
    validate_machine_model(model, active_machine, runtime_mode)
    return evaluate_machine_model_numerically(model, active_machine, feature_set)


def evaluate_machine_model_numerically(
    model: MachineModel,
    active_machine: MachineIdentity,
    feature_set: FeatureSet,
) -> MachineModelResult:
    """Apply the Step-07 numerical score after caller-owned provenance policy.

    Operational callers must continue to use :func:`evaluate_machine_model`,
    which enforces runtime-mode and model-origin policy.  This pure entry point
    exists only so the isolated external-data evaluator can exercise exactly
    the same score without granting EXTERNAL_BENCHMARK operational authority.
    """

    if model.machine.machine_id != active_machine.machine_id:
        raise ValueError(
            f"Machine model for {model.machine.machine_id} cannot score {active_machine.machine_id}"
        )
    if model.machine.family != active_machine.family:
        raise ValueError(
            f"Machine model family {model.machine.family} cannot score {active_machine.family}"
        )
    if model.machine.station_id != active_machine.station_id:
        raise ValueError(
            f"Machine model station {model.machine.station_id} cannot score {active_machine.station_id}"
        )
    if feature_set.machine != active_machine:
        raise ValueError("Feature set belongs to another installed machine")
    context = model.contexts.get(feature_set.equipment_state)
    if context is None:
        return MachineModelResult(False, (), "No healthy model for this equipment state")
    current = feature_set.by_name
    deviations: list[FeatureDeviation] = []
    for index, name in enumerate(context.feature_names):
        feature = current.get(name)
        if feature is None:
            continue
        z_score = float((feature.value - context.center[index]) / context.scale[index])
        score = float(1.0 - np.exp(-max(abs(z_score) - 1.0, 0.0) / 2.5))
        deviations.append(
            FeatureDeviation(
                feature=name,
                subsystem=context.subsystems[index],
                kind=context.kinds[index],
                value=feature.value,
                healthy_center=float(context.center[index]),
                z_score=z_score,
                score=score,
            )
        )
    if not deviations:
        return MachineModelResult(False, (), "No current features match the exact-machine model")
    return MachineModelResult(True, tuple(deviations))
