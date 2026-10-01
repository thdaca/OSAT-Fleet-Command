"""Narrow bridge to the unchanged Step07 numerical center/scale model."""
from __future__ import annotations
from typing import Sequence
import numpy as np
from ....pre_steps.pre01_common.contracts import DataOrigin, EquipmentState, MachineIdentity
from ....steps.step02_physical_features.features import FeatureSet
from ....steps.step07_machine_model.model import ContextModel, MachineModel
from .dataset_context import RealDataEvaluationError
def _fit_nominal_benchmark_model(
    identity: MachineIdentity,
    feature_sets: Sequence[FeatureSet],
) -> MachineModel:
    """Fit the unchanged Step 07 center/scale math to nominal benchmark runs.

    This deliberately does not construct Step 06 ``HealthyInterval`` or
    ``MachineHistory`` objects: the KUKA calibration runs are nominal workload
    data, not independently confirmed healthy equipment history.
    """

    if len(feature_sets) < 12:
        raise RealDataEvaluationError("Nominal benchmark baseline needs at least 12 runs")
    schema = set(feature_sets[0].by_name)
    for feature_set in feature_sets[1:]:
        schema.intersection_update(feature_set.by_name)
    names = tuple(name for name in feature_sets[0].by_name if name in schema)
    if not names:
        raise RealDataEvaluationError("Nominal benchmark runs share no usable features")
    matrix = np.asarray(
        [[row.by_name[name].value for name in names] for row in feature_sets],
        dtype=np.float64,
    )
    if not bool(np.isfinite(matrix).all()):
        raise RealDataEvaluationError("Nominal benchmark features must be finite")
    center = np.median(matrix, axis=0)
    mad = 1.4826 * np.median(np.abs(matrix - center), axis=0)
    standard = np.std(matrix, axis=0)
    floor = np.maximum(np.abs(center) * 1e-2, 1e-4)
    scale = np.where(mad > floor, mad, np.where(standard > floor, standard, floor))
    first = feature_sets[0].by_name
    context = ContextModel(
        equipment_state=EquipmentState.PROCESSING,
        feature_names=names,
        subsystems=tuple(first[name].subsystem for name in names),
        kinds=tuple(first[name].kind for name in names),
        center=np.asarray(center, dtype=np.float64),
        scale=np.asarray(scale, dtype=np.float64),
    )
    return MachineModel(
        machine=identity,
        origin=DataOrigin.EXTERNAL_BENCHMARK,
        contexts={EquipmentState.PROCESSING: context},
        physics_parameters={},
    )
