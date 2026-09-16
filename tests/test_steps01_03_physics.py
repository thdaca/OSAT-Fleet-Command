from __future__ import annotations

import datetime as dt
import unittest

import numpy as np

from osat_edge.common import EquipmentState
from osat_edge.machines import STATIONS
from osat_edge.roadmap.step01_physics_library import SLOPE, relations_for_family
from osat_edge.roadmap.step02_physical_features import extract_physical_features, robust_slope
from osat_edge.roadmap.step03_physical_residuals import (
    align_overlapping_windows,
    calculate_physical_residuals,
    fit_relation_parameters,
)
from support import NOW, identity, window


class PhysicsTests(unittest.TestCase):
    def test_library_is_small_and_family_specific(self) -> None:
        self.assertEqual(1, len(relations_for_family("wafer_saw")))
        self.assertEqual((), relations_for_family("wire_bond"))

    def test_robust_features_have_three_clear_statistics(self) -> None:
        machine = identity()
        windows = {"spindle_current": window("spindle_current", "A", list(range(61)))}
        result = extract_physical_features(
            machine,
            STATIONS["wafer_saw"],
            windows,
            timestamp=NOW,
            equipment_state=EquipmentState.PROCESSING,
            window_start=NOW - dt.timedelta(seconds=60),
        )
        self.assertEqual(3, len(result.features))
        self.assertAlmostEqual(1.0, robust_slope(windows["spindle_current"]), places=1)

    def test_alignment_uses_only_timestamp_overlap(self) -> None:
        first = window("a", "A", list(range(10)), start=0)
        second = window("b", "A", list(range(10)), start=5)
        aligned = align_overlapping_windows({"a": first, "b": second}, ("a", "b"), minimum_points=3)
        self.assertIsNotNone(aligned)
        self.assertEqual(5, len(aligned["a"]))
        self.assertEqual(5.0, aligned["a"][0])

    def test_alignment_never_extrapolates_disjoint_signals(self) -> None:
        first = window("a", "A", [1] * 10, start=0)
        second = window("b", "A", [2] * 10, start=20)
        self.assertIsNone(align_overlapping_windows({"a": first, "b": second}, ("a", "b")))

    def test_current_speed_fit_and_residual_are_exact_machine_parameters(self) -> None:
        speed = np.linspace(20_000, 21_000, 60)
        current = 1.5 + 0.0002 * speed
        windows = {
            "spindle_speed": window("spindle_speed", "RPM", speed),
            "spindle_current": window("spindle_current", "A", current),
        }
        parameters = fit_relation_parameters("wafer_saw", "spindle.current_speed_residual", windows)
        residuals = calculate_physical_residuals(
            "wafer_saw", windows, fitted_parameters={"spindle.current_speed_residual": parameters}
        )
        self.assertAlmostEqual(0.0002, parameters[SLOPE], places=6)
        self.assertAlmostEqual(0.0, residuals[0].value, places=4)

    def test_wrong_units_suppress_physics_evidence(self) -> None:
        speed = np.linspace(20_000, 21_000, 60)
        windows = {
            "spindle_speed": window("spindle_speed", "rad/s", speed),
            "spindle_current": window("spindle_current", "A", 1.5 + 0.0002 * speed),
        }
        self.assertEqual((), calculate_physical_residuals("wafer_saw", windows))


if __name__ == "__main__":
    unittest.main()
