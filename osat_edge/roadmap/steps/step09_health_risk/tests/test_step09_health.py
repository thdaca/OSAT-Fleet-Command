from __future__ import annotations

import datetime as dt
import unittest

from osat_edge.roadmap.pre_steps.pre01_common.pre01_common import EquipmentState, HealthState, RuntimeMode
from osat_edge.roadmap.pre_steps.pre02_machine_registry.pre02_machine_registry import STATIONS
from osat_edge.roadmap.steps.step09_health_risk.step09_health_risk import HealthEngine, StateTracker
from osat_edge.roadmap.steps.step08_live_telemetry.step08_live_telemetry import TelemetryStatus
from osat_edge.roadmap.pre_steps.pre01_common.tests.support import NOW, good_status, identity, model_result


class HealthTests(unittest.TestCase):
    def engine(self) -> HealthEngine:
        return HealthEngine(identity(), STATIONS["wafer_saw"])

    def assess(self, engine: HealthEngine, second: int, score: float | None, **kwargs):
        return engine.assess(
            good_status(),
            None if score is None else model_result(score),
            timestamp=NOW + dt.timedelta(seconds=second),
            runtime_mode=kwargs.get("runtime_mode", RuntimeMode.SIMULATION),
            equipment_state=EquipmentState.PROCESSING,
            family_risk_score=kwargs.get("family_risk_score"),
        )

    def test_missing_exact_machine_model_means_unknown(self) -> None:
        result = self.assess(self.engine(), 0, None)
        self.assertEqual(HealthState.UNKNOWN, result.health_state)

    def test_invalid_telemetry_forces_unknown(self) -> None:
        engine = self.engine()
        result = engine.assess(
            TelemetryStatus(False, False, frozenset(), ("spindle_current: stale",)),
            model_result(0.9),
            timestamp=NOW,
            runtime_mode=RuntimeMode.SIMULATION,
            equipment_state=EquipmentState.PROCESSING,
        )
        self.assertEqual(HealthState.UNKNOWN, result.health_state)

    def test_subsystem_fault_remains_localized(self) -> None:
        engine = self.engine()
        self.assess(engine, 0, 0.9)
        self.assess(engine, 1, 0.9)
        result = self.assess(engine, 2, 0.9)
        self.assertEqual(HealthState.CRITICAL, result.health_state)
        self.assertEqual(("spindle",), result.suspected_subsystems)

    def test_global_family_risk_does_not_fake_subsystem_attribution(self) -> None:
        engine = self.engine()
        self.assess(engine, 0, 0.0, family_risk_score=0.9)
        self.assess(engine, 1, 0.0, family_risk_score=0.9)
        result = self.assess(engine, 2, 0.0, family_risk_score=0.9)
        self.assertEqual(HealthState.NORMAL, result.health_state)
        self.assertEqual((), result.suspected_subsystems)
        self.assertEqual(0.9, result.family_risk_score)
        self.assertIn("advisory", result.reason)
        self.assertIn("does not alter", result.reason)

    def test_nonfinite_scores_force_unknown(self) -> None:
        for score in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(score=score):
                state, _ = StateTracker().update(score, NOW)
                self.assertEqual(HealthState.UNKNOWN, state)

    def test_health_timestamps_cannot_move_backward(self) -> None:
        tracker = StateTracker()
        tracker.update(0.0, NOW)
        with self.assertRaisesRegex(ValueError, "backward"):
            tracker.update(0.0, NOW - dt.timedelta(seconds=1))

    def test_unknown_gap_resets_pending_hysteresis(self) -> None:
        tracker = StateTracker()
        tracker.update(0.9, NOW)
        tracker.update(None, NOW + dt.timedelta(seconds=1))
        state, _ = tracker.update(0.9, NOW + dt.timedelta(seconds=2))
        self.assertEqual(HealthState.UNKNOWN, state)
        state, _ = tracker.update(0.9, NOW + dt.timedelta(seconds=4))
        self.assertEqual(HealthState.CRITICAL, state)

    def test_live_assessment_is_plainly_observe_only(self) -> None:
        engine = self.engine()
        self.assess(engine, 0, 0.0, runtime_mode=RuntimeMode.LIVE_EQUIPMENT)
        self.assess(engine, 1, 0.0, runtime_mode=RuntimeMode.LIVE_EQUIPMENT)
        result = self.assess(engine, 2, 0.0, runtime_mode=RuntimeMode.LIVE_EQUIPMENT)
        self.assertIn("OBSERVE ONLY", result.reason)


if __name__ == "__main__":
    unittest.main()
