from __future__ import annotations

import datetime as dt
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from osat_edge.common import DataOrigin, EquipmentState, HealthState, OperatingContext, RuntimeMode, TelemetrySample, VERSION
from osat_edge.demo import create_demo_fleet, run_demo
from osat_edge.machines import STATIONS
from osat_edge.pipeline import MachinePipeline
from osat_edge.roadmap.step01_physics_library import SPEED_HIGH, SPEED_LOW
from osat_edge.roadmap.step05_family_model import FamilyModel
from osat_edge.roadmap.step11a_maintenance_db import MaintenanceRepository
from osat_edge.roadmap.step15_maintenance_ticket import list_tickets
from osat_edge.roadmap.step08_live_telemetry import QueuedTelemetrySource, ReplayTelemetrySource, TelemetryBatch
from support import NOW, identity


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

    def test_ws_transition_keeps_speed_in_domain_and_emits_local_physics_evidence(self) -> None:
        demo = create_demo_fleet()
        try:
            machine = demo.pipeline.machines["wafer_saw"]
            relation_id = "spindle.current_speed_residual"
            parameters = machine.machine_model.physics_parameters[relation_id]
            demo.inject_ws_spindle()
            first_abnormal = None
            final = None
            for _ in range(75):
                final = demo.tick()["wafer_saw"]
                if (
                    first_abnormal is None
                    and final.assessment.health_state
                    in {HealthState.DEGRADED, HealthState.CRITICAL}
                ):
                    first_abnormal = final
                    latest_speed = machine.store.latest("spindle_speed")
                    self.assertIsNotNone(latest_speed)
                    self.assertGreaterEqual(latest_speed.value, parameters[SPEED_LOW])
                    self.assertLessEqual(latest_speed.value, parameters[SPEED_HIGH])
                    physics = [
                        feature for feature in final.feature_set.features
                        if feature.relation_id == relation_id
                    ]
                    self.assertTrue(physics)
                    deviations = [
                        deviation
                        for subsystem in final.assessment.subsystem_health
                        for deviation in subsystem.deviations
                        if deviation.feature == physics[0].name
                    ]
                    self.assertTrue(deviations)
                    self.assertEqual(("spindle",), final.assessment.suspected_subsystems)
            self.assertIsNotNone(first_abnormal)
            self.assertEqual(HealthState.CRITICAL, final.assessment.health_state)
            tickets = list_tickets(demo.pipeline.repository)
            self.assertEqual(1, len(tickets))
            self.assertEqual("URGENT", tickets[0].priority)
            self.assertTrue(
                all("spindle" in item for item in tickets[0].evidence_descriptions)
            )
            self.assertTrue(
                all("above" in item or "below" in item for item in tickets[0].evidence_descriptions)
            )
        finally:
            demo.close()

    def test_delayed_live_batch_is_stale_against_wall_clock(self) -> None:
        machine = identity()
        station = STATIONS["wafer_saw"]
        source = QueuedTelemetrySource(machine, station)
        samples = []
        for second in range(3):
            for spec in station.channels:
                if spec.required:
                    samples.append(
                        TelemetrySample(
                            machine.machine_id,
                            spec.name,
                            NOW + dt.timedelta(seconds=second),
                            1.0 if spec.unit != "RPM" else 20_000.0,
                            spec.unit,
                            spec.source_id,
                        )
                    )
        source.submit(
            samples,
            context=OperatingContext(
                machine.machine_id,
                NOW + dt.timedelta(seconds=2),
                EquipmentState.PROCESSING,
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            pipeline = MachinePipeline(
                identity=machine,
                station=station,
                source=source,
                repository=MaintenanceRepository(Path(directory) / "live.sqlite"),
            )
            result = pipeline.tick(wall_now=NOW + dt.timedelta(hours=1))
        self.assertIsNotNone(result)
        self.assertFalse(result.telemetry_status.valid)
        self.assertTrue(any("stale" in issue for issue in result.telemetry_status.issues))
        self.assertIs(RuntimeMode.LIVE_EQUIPMENT, result.assessment.runtime_mode)

    def test_replay_exhaustion_returns_none_and_preserves_last_result(self) -> None:
        machine = identity()
        station = STATIONS["wafer_saw"]
        spec = station.channels[0]
        batch = TelemetryBatch(
            (
                TelemetrySample(
                    machine.machine_id, spec.name, NOW, 1.0,
                    spec.unit, spec.source_id,
                ),
            ),
            OperatingContext(machine.machine_id, NOW, EquipmentState.PROCESSING),
        )
        source = ReplayTelemetrySource(
            machine, station, (batch,), origin=DataOrigin.REAL_OSAT
        )
        with tempfile.TemporaryDirectory() as directory:
            pipeline = MachinePipeline(
                identity=machine,
                station=station,
                source=source,
                repository=MaintenanceRepository(Path(directory) / "replay.sqlite"),
            )
            previous = pipeline.tick()
            self.assertIsNotNone(previous)
            self.assertIsNone(pipeline.tick())
            self.assertIs(previous, pipeline.last_result)

    def test_deterministic_ticket_exists_before_optional_llm_call(self) -> None:
        demo = create_demo_fleet()
        observed = []

        def inspect_repository(evidence, passages, *, model_path):
            observed.append(
                demo.pipeline.repository.active_for_machine(evidence.machine.machine_id)
            )
            return None

        try:
            demo.inject_ws_spindle()
            with patch(
                "osat_edge.pipeline.generate_local_llm_json",
                side_effect=inspect_repository,
            ):
                for _ in range(75):
                    demo.tick()
            self.assertTrue(observed)
            self.assertTrue(all(ticket is not None for ticket in observed))
            self.assertTrue(
                all(ticket["explanation_backend"] == "deterministic-fallback" for ticket in observed)
            )
        finally:
            demo.close()

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
