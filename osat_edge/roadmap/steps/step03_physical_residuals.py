"""Step 03: timestamp-overlap alignment and physical residual features."""

from __future__ import annotations

from typing import Mapping

import numpy as np

from ..pre_steps.pre01_common import ChannelWindow
from .step01_physics_library import PhysicsRelation, relations_for_family
from .step02_physical_features import Feature


def align_overlapping_windows(
    windows: Mapping[str, ChannelWindow],
    channels: tuple[str, ...],
    *,
    minimum_points: int = 8,
) -> dict[str, np.ndarray] | None:
    """Align signals only inside their shared timestamp interval."""

    if any(channel not in windows or len(windows[channel].timestamps) < 2 for channel in channels):
        return None
    start = max(float(windows[channel].timestamps[0]) for channel in channels)
    end = min(float(windows[channel].timestamps[-1]) for channel in channels)
    if end <= start:
        return None
    reference = max(
        channels,
        key=lambda name: int(
            np.sum(
                (windows[name].timestamps >= start)
                & (windows[name].timestamps <= end)
            )
        ),
    )
    query = windows[reference].timestamps
    query = query[(query >= start) & (query <= end)]
    if len(query) < minimum_points:
        return None
    aligned: dict[str, np.ndarray] = {}
    for channel in channels:
        window = windows[channel]
        mask = (window.timestamps >= start) & (window.timestamps <= end)
        support_t = window.timestamps[mask]
        support_v = window.values[mask]
        if len(support_t) < 2:
            return None
        inside = (query >= support_t[0]) & (query <= support_t[-1])
        if not bool(np.all(inside)):
            return None
        aligned[channel] = np.interp(query, support_t, support_v)
    return aligned


def _aligned_for_relation(
    relation: PhysicsRelation,
    windows: Mapping[str, ChannelWindow],
    *,
    minimum_points: int,
) -> dict[str, np.ndarray] | None:
    if any(
        windows.get(channel) is None or windows[channel].unit != unit
        for channel, unit in relation.expected_units
    ):
        return None
    return align_overlapping_windows(
        windows, relation.required_channels, minimum_points=minimum_points
    )


def fit_relation_parameters(
    family: str,
    relation_id: str,
    windows: Mapping[str, ChannelWindow],
) -> dict[str, float]:
    relation = next(
        (item for item in relations_for_family(family) if item.relation_id == relation_id),
        None,
    )
    if relation is None or relation.fit is None:
        raise ValueError(f"No fitted relation {relation_id!r} exists for {family}")
    aligned = _aligned_for_relation(relation, windows, minimum_points=20)
    if aligned is None:
        raise ValueError("At least 20 timestamp-overlapping samples are required")
    return {name: float(value) for name, value in relation.fit(aligned).items()}


def calculate_physical_residuals(
    family: str,
    windows: Mapping[str, ChannelWindow],
    *,
    fitted_parameters: Mapping[str, Mapping[str, float]] | None = None,
) -> tuple[Feature, ...]:
    parameters = fitted_parameters or {}
    features: list[Feature] = []
    for relation in relations_for_family(family):
        if relation.fit is not None and relation.relation_id not in parameters:
            continue
        aligned = _aligned_for_relation(relation, windows, minimum_points=8)
        if aligned is None:
            continue
        output = relation.compute(aligned, parameters.get(relation.relation_id, {}))
        for name, value in output.items():
            if np.isfinite(value):
                features.append(
                    Feature(
                        name=name,
                        value=float(value),
                        subsystem=relation.subsystem,
                        kind="physics",
                        relation_id=relation.relation_id,
                    )
                )
    return tuple(features)
