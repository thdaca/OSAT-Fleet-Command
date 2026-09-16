from __future__ import annotations

import datetime as dt
import unittest
from dataclasses import replace

from osat_edge.common import DataOrigin, RuntimeMode
from osat_edge.roadmap.step04_family_data import FamilyDataset, FamilySample
from osat_edge.roadmap.step05_family_model import fit_family_model, score_family_model
from osat_edge.roadmap.step06_machine_history import HealthyInterval, MachineHistory
from osat_edge.roadmap.step07_machine_model import evaluate_machine_model, fit_machine_model
from support import NOW, family_dataset, feature_set, identity


class ModelTests(unittest.TestCase):
    def test_family_samples_require_one_schema(self) -> None:
        data = family_dataset()
        bad = replace(data.samples[-1], features={"different": 1.0})
        with self.assertRaises(ValueError):
            replace(data, samples=data.samples[:-1] + (bad,))

    def test_positive_windows_reference_observed_events(self) -> None:
        data = family_dataset()
        bad = replace(data.samples[0], future_event_id="not-recorded")
        with self.assertRaises(ValueError):
            replace(data, samples=(bad,) + data.samples[1:])

    def test_family_records_must_lie_inside_collection_period(self) -> None:
        data = family_dataset()
        outside_sample = replace(data.samples[0], timestamp=data.collected_start - dt.timedelta(seconds=1))
        outside_event = replace(data.events[0], timestamp=data.collected_end + dt.timedelta(seconds=1))
        with self.assertRaisesRegex(ValueError, "collection period"):
            replace(data, samples=(outside_sample,) + data.samples[1:])
        with self.assertRaisesRegex(ValueError, "collection period"):
            replace(data, events=(outside_event,) + data.events[1:])

    def test_positive_window_must_precede_its_referenced_event(self) -> None:
        data = family_dataset()
        positive_index = next(
            index for index, sample in enumerate(data.samples) if sample.future_event_id
        )
        event = next(
            event
            for event in data.events
            if event.machine_id == data.samples[positive_index].machine_id
        )
        leaked = replace(
            data.samples[positive_index],
            timestamp=event.timestamp + dt.timedelta(seconds=1),
        )
        samples = data.samples[:positive_index] + (leaked,) + data.samples[positive_index + 1:]
        with self.assertRaisesRegex(ValueError, "occur after"):
            replace(data, samples=samples)

    def test_family_training_is_real_only(self) -> None:
        with self.assertRaisesRegex(ValueError, "REAL_OSAT"):
            fit_family_model(family_dataset(DataOrigin.SYNTHETIC))

    def test_real_family_model_returns_risk_score(self) -> None:
        model = fit_family_model(family_dataset())
        score = score_family_model(
            model,
            active_family="wafer_saw",
            features={"current": 5.0, "vibration": 7.0},
            runtime_mode=RuntimeMode.LIVE_EQUIPMENT,
        )
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_each_held_out_machine_must_leave_both_training_classes(self) -> None:
        data = family_dataset()
        samples = tuple(
            replace(sample, future_event_id=None)
            if sample.machine_id == "WS-01"
            else replace(sample, future_event_id=f"bearing-{int(sample.machine_id[-2:]) - 1}")
            for sample in data.samples
        )
        data = replace(data, samples=samples)
        with self.assertRaisesRegex(ValueError, "held-out-machine"):
            fit_family_model(
                data,
                minimum_independent_events=2,
                minimum_positive_windows=2,
            )

    def test_family_identity_mismatch_is_rejected(self) -> None:
        model = fit_family_model(family_dataset())
        with self.assertRaisesRegex(ValueError, "cannot score"):
            score_family_model(model, active_family="wire_bond", features={}, runtime_mode=RuntimeMode.SIMULATION)

    def test_synthetic_family_model_is_rejected_on_live_or_replay(self) -> None:
        model = replace(fit_family_model(family_dataset()), origin=DataOrigin.SYNTHETIC)
        for mode in (RuntimeMode.REAL_REPLAY, RuntimeMode.LIVE_EQUIPMENT):
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, "synthetic"):
                score_family_model(model, active_family="wafer_saw", features={"current": 1, "vibration": 1}, runtime_mode=mode)

    def test_healthy_window_must_be_fully_contained(self) -> None:
        machine = identity()
        interval = HealthyInterval(machine.machine_id, NOW, NOW + dt.timedelta(seconds=100))
        inside = feature_set(machine, start=NOW + dt.timedelta(seconds=10), end=NOW + dt.timedelta(seconds=70))
        crossing = feature_set(machine, start=NOW + dt.timedelta(seconds=50), end=NOW + dt.timedelta(seconds=110))
        history = MachineHistory(machine, DataOrigin.SYNTHETIC, (inside, crossing), (interval,))
        self.assertEqual((inside,), history.healthy_feature_sets())

    def test_machine_history_cannot_mix_installed_machines(self) -> None:
        machine = identity(machine_id="WS-01")
        interval = HealthyInterval(machine.machine_id, NOW, NOW + dt.timedelta(hours=1))
        with self.assertRaisesRegex(ValueError, "mix"):
            MachineHistory(machine, DataOrigin.SYNTHETIC, (feature_set(identity(machine_id="WS-02")),), (interval,))

    def test_exact_machine_model_rejects_other_machine_and_live_synthetic_use(self) -> None:
        machine = identity(machine_id="WS-01")
        rows = tuple(feature_set(machine, value=10 + index * 0.1, start=NOW + dt.timedelta(minutes=index)) for index in range(12))
        interval = HealthyInterval(machine.machine_id, NOW, NOW + dt.timedelta(hours=2))
        model = fit_machine_model(MachineHistory(machine, DataOrigin.SYNTHETIC, rows, (interval,)))
        with self.assertRaisesRegex(ValueError, "cannot score"):
            evaluate_machine_model(model, identity(machine_id="WS-02"), rows[-1], runtime_mode=RuntimeMode.SIMULATION)
        wrong_station = replace(machine, station_id="WS-99")
        with self.assertRaisesRegex(ValueError, "station"):
            evaluate_machine_model(model, wrong_station, replace(rows[-1], machine=wrong_station), runtime_mode=RuntimeMode.SIMULATION)
        with self.assertRaisesRegex(ValueError, "synthetic"):
            evaluate_machine_model(model, machine, rows[-1], runtime_mode=RuntimeMode.LIVE_EQUIPMENT)
        self.assertTrue(evaluate_machine_model(model, machine, rows[-1], runtime_mode=RuntimeMode.SIMULATION).available)


if __name__ == "__main__":
    unittest.main()
