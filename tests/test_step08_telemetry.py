from __future__ import annotations

import datetime as dt
import unittest

from osat_edge.common import EquipmentState, OperatingContext, TelemetrySample
from osat_edge.machines import STATIONS
from osat_edge.roadmap.step08_live_telemetry import (
    BoundedTelemetryStore,
    NoNewTelemetry,
    QueuedTelemetrySource,
    ReplayTelemetrySource,
    SecsGemAdapter,
    TelemetryBatch,
    TelemetryError,
    TelemetrySecurityError,
    TelemetrySourceExhausted,
    assess_telemetry,
)
from support import NOW, identity


class TelemetryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.machine = identity("wafer_saw")
        self.station = STATIONS["wafer_saw"]
        self.store = BoundedTelemetryStore(self.machine, self.station, maximum_samples_per_channel=4)

    def sample(self, channel: str, second: int, value: float = 1.0) -> TelemetrySample:
        spec = next(item for item in self.station.channels if item.name == channel)
        return TelemetrySample(self.machine.machine_id, channel, NOW + dt.timedelta(seconds=second), value, spec.unit, spec.source_id)

    def fill_required(self, seconds: range = range(3)) -> None:
        for second in seconds:
            for channel in ("spindle_current", "spindle_speed", "coolant_pressure"):
                self.store.append(self.sample(channel, second))
        self.store.append_context(OperatingContext(self.machine.machine_id, NOW + dt.timedelta(seconds=max(seconds)), EquipmentState.PROCESSING))

    def test_async_streams_are_independent_and_bounded(self) -> None:
        for second in range(6):
            self.store.append(self.sample("spindle_current", second, second))
        self.store.append(self.sample("coolant_pressure", 0, 2.0))
        current = self.store.window("spindle_current", end=NOW + dt.timedelta(seconds=6))
        coolant = self.store.window("coolant_pressure", end=NOW + dt.timedelta(seconds=6))
        self.assertEqual(4, len(current.values))
        self.assertEqual(1, len(coolant.values))

    def test_store_rejects_wrong_machine_unit_and_timestamp_order(self) -> None:
        with self.assertRaises(TelemetryError):
            self.store.append(TelemetrySample("OTHER", "spindle_current", NOW, 1, "A", "WS-SV-01"))
        with self.assertRaises(TelemetryError):
            self.store.append(TelemetrySample(self.machine.machine_id, "spindle_current", NOW, 1, "V", "WS-SV-01"))
        with self.assertRaises(TelemetrySecurityError):
            self.store.append(TelemetrySample(self.machine.machine_id, "spindle_current", NOW, 1, "A", "UNREVIEWED"))
        self.store.append(self.sample("spindle_current", 1))
        with self.assertRaises(TelemetryError):
            self.store.append(self.sample("spindle_current", 1))

    def test_missing_required_channel_is_invalid(self) -> None:
        self.store.append_context(OperatingContext(self.machine.machine_id, NOW, EquipmentState.PROCESSING))
        status = assess_telemetry(self.store, now=NOW)
        self.assertFalse(status.valid)
        self.assertFalse(status.observable)

    def test_stale_required_channel_is_invalid(self) -> None:
        self.fill_required()
        status = assess_telemetry(self.store, now=NOW + dt.timedelta(seconds=20))
        self.assertFalse(status.valid)
        self.assertTrue(any("stale" in issue for issue in status.issues))

    def test_missing_optional_channels_do_not_invalidate(self) -> None:
        self.fill_required()
        status = assess_telemetry(self.store, now=NOW + dt.timedelta(seconds=2))
        self.assertTrue(status.valid)
        self.assertTrue(status.observable)

    def test_stale_operating_context_is_not_observable(self) -> None:
        for second in range(33, 36):
            for channel in ("spindle_current", "spindle_speed", "coolant_pressure"):
                self.store.append(self.sample(channel, second))
        self.store.append_context(OperatingContext(self.machine.machine_id, NOW, EquipmentState.PROCESSING))
        status = assess_telemetry(self.store, now=NOW + dt.timedelta(seconds=35))
        self.assertTrue(status.valid)
        self.assertFalse(status.observable)

    def test_live_and_replay_sources_have_explicit_empty_semantics(self) -> None:
        live = QueuedTelemetrySource(self.machine, self.station)
        with self.assertRaises(NoNewTelemetry):
            live.poll()
        batch = TelemetryBatch((self.sample("spindle_current", 0),))
        replay = ReplayTelemetrySource(self.machine, self.station, (batch,))
        self.assertEqual(batch, replay.poll())
        with self.assertRaises(TelemetrySourceExhausted):
            replay.poll()

    def test_secs_adapter_accepts_only_approved_source_ids(self) -> None:
        adapter = SecsGemAdapter(self.machine, self.station)
        samples = adapter.parse({"stream": 6, "function": 11, "variables": [{"id": "WS-SV-01", "value": 2.5}]}, received_at=NOW)
        self.assertEqual("spindle_current", samples[0].channel)
        with self.assertRaises(TelemetrySecurityError):
            adapter.parse({"variables": [{"id": "UNREVIEWED", "value": 2.5}]}, received_at=NOW)

    def test_secs_adapter_rejects_process_ip_anywhere(self) -> None:
        adapter = SecsGemAdapter(self.machine, self.station)
        for payload in ({"recipe": "secret"}, {"metadata": {"name": "wafer-map"}}):
            with self.subTest(payload=payload), self.assertRaises(TelemetrySecurityError):
                adapter.parse(payload, received_at=NOW)

    def test_secs_adapter_rejects_other_messages_and_bad_mapping(self) -> None:
        with self.assertRaises(ValueError):
            SecsGemAdapter(self.machine, self.station, {"X": "recipe_id"})
        adapter = SecsGemAdapter(self.machine, self.station)
        with self.assertRaises(ValueError):
            adapter.parse({"stream": 1, "function": 1, "variables": []}, received_at=NOW)


if __name__ == "__main__":
    unittest.main()
