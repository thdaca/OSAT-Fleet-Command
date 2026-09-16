from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from osat_edge.common import DataOrigin, HealthState, VERSION
from osat_edge.demo import create_demo_fleet, run_demo
from osat_edge.pipeline import MachinePipeline
from osat_edge.roadmap.step05_family_model import FamilyModel
from osat_edge.roadmap.step11a_maintenance_db import MaintenanceRepository


class PipelineDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.demo = create_demo_fleet()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.demo.close()

    def test_fleet_contains_the_nine_isolated_stations(self) -> None:
        self.assertEqual(9, len(self.demo.pipeline.machines))
        self.assertEqual(9, len({machine.identity.machine_id for machine in self.demo.pipeline.machines.values()}))

    def test_nominal_deterministic_fleet_is_normal_without_tickets(self) -> None:
        states = {machine.last_result.assessment.health_state.value for machine in self.demo.pipeline.machines.values()}
        self.assertEqual({"NORMAL"}, states)
        self.assertEqual([], self.demo.pipeline.repository.list_tickets())

    def test_result_exposes_the_status_and_features_used_by_inference(self) -> None:
        result = self.demo.pipeline.machines["wafer_saw"].last_result
        self.assertIsNotNone(result)
        self.assertTrue(result.telemetry_status.valid)
        self.assertTrue(result.telemetry_status.observable)
        self.assertIsNotNone(result.feature_set)
        self.assertEqual("DEMO-WS-01", result.feature_set.machine.machine_id)

    def test_disconnect_stops_current_assessment_but_keeps_last_results(self) -> None:
        previous = self.demo.pipeline.machines["wafer_saw"].last_result
        self.demo.pipeline.set_connected(False)
        self.assertEqual({}, self.demo.tick())
        self.assertIs(previous, self.demo.pipeline.machines["wafer_saw"].last_result)
        self.demo.pipeline.set_connected(True)

    def test_monitor_isolate_affects_only_selected_machine(self) -> None:
        self.demo.pipeline.set_monitored("wire_bond", False)
        results = self.demo.tick()
        self.assertNotIn("wire_bond", results)
        self.assertIn("wafer_saw", results)
        self.demo.pipeline.set_monitored("wire_bond", True)

    def test_missing_optional_family_feature_skips_only_family_scoring(self) -> None:
        machine = self.demo.pipeline.machines["wafer_saw"]
        previous_model = machine.family_model
        machine.family_model = FamilyModel(
            family="wafer_saw",
            origin=DataOrigin.SYNTHETIC,
            feature_names=("missing_optional.median",),
            scaler_center=np.asarray([0.0]),
            scaler_scale=np.asarray([1.0]),
            coefficients=np.asarray([1.0]),
            intercept=40.0,
        )
        try:
            result = machine.tick()
        finally:
            machine.family_model = previous_model
        self.assertIsNotNone(result)
        self.assertEqual(HealthState.NORMAL, result.assessment.health_state)
        self.assertIsNone(result.assessment.family_risk_score)

    def test_public_demo_reaches_localized_critical_and_one_urgent_ticket(self) -> None:
        result = run_demo()
        self.assertEqual(VERSION, result["version"])
        self.assertEqual("CRITICAL", result["states"]["wafer_saw"])
        self.assertEqual(["spindle"], result["ws01_subsystems"])
        self.assertEqual(1, len(result["tickets"]))
        self.assertEqual("URGENT", result["tickets"][0]["priority"])

    def test_pipeline_rejects_identity_profile_mismatch(self) -> None:
        machine = self.demo.pipeline.machines["wafer_saw"]
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
            MachinePipeline(
                identity=machine.identity,
                station=self.demo.pipeline.machines["wire_bond"].station,
                source=machine.source,
                repository=MaintenanceRepository(Path(directory) / "x.sqlite"),
            )


if __name__ == "__main__":
    unittest.main()
