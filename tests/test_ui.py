from __future__ import annotations

import os
import unittest
from dataclasses import replace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from osat_edge.common import HealthState, VERSION
from osat_edge.machines import STATIONS
from osat_edge.ui import FleetCommandWindow, HEALTH_COLOR, PALETTE, TelemetryTrend


def _relative_luminance(color: str) -> float:
    channels = [int(color[index:index + 2], 16) / 255.0 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(first: str, second: str) -> float:
    light, dark = sorted((_relative_luminance(first), _relative_luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def _table_text(table) -> str:
    return "\n".join(
        table.item(row, column).text()
        for row in range(table.rowCount())
        for column in range(table.columnCount())
        if table.item(row, column) is not None
    )


class UiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])
        cls.window = FleetCommandWindow()
        cls.window.inference_timer.stop()
        cls.window.paint_timer.stop()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.window.close()
        cls.application.processEvents()

    def test_palette_text_colors_have_readable_contrast(self) -> None:
        for name in ("amber", "amber_muted", "watch", "degraded", "critical", "unknown"):
            with self.subTest(name=name):
                self.assertGreaterEqual(_contrast(PALETTE[name], PALETTE["background"]), 4.5)

    def test_exact_five_screen_hierarchy_and_research_header(self) -> None:
        self.assertEqual(
            ["FLEET", "MACHINE", "PHYSICS", "MAINTENANCE", "SYSTEM"],
            [self.window.tabs.tabText(index) for index in range(self.window.tabs.count())],
        )
        self.assertIn(VERSION, self.window.windowTitle())
        self.assertIn("RESEARCH / DEVELOPMENT", self.window.windowTitle())
        self.assertIn("DEMO TICKETS ONLY", self.window.authority_label.text())

    def test_ui_has_nine_named_cards_and_text_for_every_health_state(self) -> None:
        self.assertEqual(9, len(self.window.cards))
        card_text = " ".join(card.title_label.text() for card in self.window.cards.values())
        for station in STATIONS.values():
            self.assertIn(station.station_id, card_text)
        card = self.window.cards["wafer_saw"]
        result = self.window.pipeline.machines["wafer_saw"].last_result
        self.assertIsNotNone(result)
        for state in HealthState:
            assessment = replace(result.assessment, health_state=state)
            card.update_assessment(
                assessment,
                monitored=True,
                connected=True,
                telemetry_valid=True,
                observable=True,
                assessment_age=0.0,
            )
            self.assertIn(state.value, card.health.text())
            self.assertIn(state, HEALTH_COLOR)
        self.window._paint()

    def test_ws01_telemetry_table_exposes_every_canonical_channel(self) -> None:
        self.window._select("wafer_saw")
        rows = {
            self.window.telemetry_table.item(row, 0).text(): tuple(
                self.window.telemetry_table.item(row, column).text()
                for column in range(self.window.telemetry_table.columnCount())
            )
            for row in range(self.window.telemetry_table.rowCount())
        }
        self.assertEqual({item.name for item in STATIONS["wafer_saw"].channels}, set(rows))
        for spec in STATIONS["wafer_saw"].channels:
            self.assertEqual(spec.unit, rows[spec.name][3])
            self.assertEqual("REQUIRED" if spec.required else "OPTIONAL", rows[spec.name][4])
            self.assertEqual(spec.source_id, rows[spec.name][5])
            self.assertTrue(rows[spec.name][6])
            self.assertTrue(rows[spec.name][7])

    def test_model_boundary_is_transparent_without_internal_arrays(self) -> None:
        text = self.window.model_status.toPlainText()
        self.assertIn("EXACT-MACHINE MODEL", text)
        self.assertIn("STATUS: LOADED", text)
        self.assertIn("DATA ORIGIN", text)
        self.assertIn("UNCALIBRATED", text)
        for hidden in ("COEFFICIENT", "CENTER VECTOR", "SCALE ARRAY", "CLASSIFIER WEIGHT"):
            self.assertNotIn(hidden, text)

    def test_physics_exposes_runtime_maturity_value_and_research_blocker(self) -> None:
        self.window._select("wafer_saw")
        text = _table_text(self.window.physics_table)
        self.assertIn("spindle.current_speed_residual", text)
        self.assertIn("RUNTIME_RESEARCH", text)
        self.assertIn("LITERATURE_SUPPORTED", text)
        self.assertIn("A", text)
        self.assertNotIn("N/A — NOT RUNTIME\nA\n", text)
        detail = self.window.physics_detail.toPlainText()
        self.assertIn("MAJOR BLOCKER", detail)
        self.assertIn("NEXT EXPERIMENT", detail)
        self.assertIn("MEASUREMENT UNCERTAINTY SOURCES", detail)
        self.assertIn("MODEL DISCREPANCY SOURCES", detail)
        self.assertIn("FALSIFICATION CRITERIA", detail)

    def test_family_without_runtime_physics_keeps_rejected_catalog_visible(self) -> None:
        self.window._select("wire_bond")
        text = _table_text(self.window.physics_table)
        self.assertIn("wire_bond.ultrasonic_input_impedance", text)
        self.assertIn("REJECTED", text)
        self.assertIn("N/A — NOT RUNTIME", text)
        detail = self.window.physics_detail.toPlainText()
        self.assertIn("MAJOR BLOCKER", detail)
        self.assertNotIn("NOT AVAILABLE\n\nNEXT EXPERIMENT\nNOT AVAILABLE", detail)
        self.window._select("wafer_saw")

    def test_disconnect_marks_last_known_and_excludes_cached_health_counts(self) -> None:
        self.window._toggle_link()
        try:
            card = self.window.cards["wafer_saw"]
            self.assertEqual("DISCONNECTED", card.health.text())
            self.assertIn("LAST KNOWN:", card.telemetry.text())
            self.assertEqual("NORMAL 0", self.window.summary_labels["NORMAL"].text())
            self.assertEqual("UNKNOWN 9", self.window.summary_labels["UNKNOWN"].text())
            self.assertIn("LAST KNOWN ASSESSMENT", self.window.machine_status.text())
            self.assertIn("LAST KNOWN PHYSICS EVIDENCE", self.window.physics_status.text())
        finally:
            self.window._toggle_link()
        self.assertIn("CONNECTED", self.window.connection_label.text())
        self.assertEqual("NORMAL 9", self.window.summary_labels["NORMAL"].text())

    def test_monitor_control_isolates_only_one_card(self) -> None:
        card = self.window.cards["wire_bond"]
        card.monitor.setChecked(False)
        self.window._paint()
        self.assertFalse(self.window.pipeline.machines["wire_bond"].monitored)
        self.assertIn("ISOLATED", card.health.text())
        self.assertTrue(self.window.pipeline.machines["wafer_saw"].monitored)
        card.monitor.setChecked(True)
        self.window._paint()

    def test_system_tab_states_real_runtime_security_and_authority_facts(self) -> None:
        text = self.window.system_text.toPlainText()
        for required in (
            VERSION,
            "RUNTIME MODE: SIMULATION",
            "CONNECTION STATE: CONNECTED",
            "DEMO TICKETS ONLY",
            "EXACT-MACHINE MODEL ORIGIN: SYNTHETIC",
            "UNKNOWN SOURCE IDs ARE REJECTED",
            "RUNTIME NETWORK DEPENDENCY: NONE",
            "LLM HAS NO HEALTH-DECISION AUTHORITY",
            "MODEL INTERNAL ALGORITHM / FITTED INTERNALS NOT DISPLAYED",
        ):
            self.assertIn(required, text)
        self.assertNotIn("AIR-GAPPED", text)
        self.assertNotIn("SAFETY CERTIFIED", text)

    def test_accessible_names_cover_primary_monitoring_controls(self) -> None:
        widgets = (
            self.window.tabs,
            self.window.fleet_area,
            self.window.telemetry_table,
            self.window.physics_table,
            self.window.ticket_table,
            self.window.link_button,
            self.window.inject_button,
        )
        self.assertTrue(all(widget.accessibleName().strip() for widget in widgets))

    def test_1280_by_720_layout_processes_without_losing_navigation(self) -> None:
        self.window.resize(1280, 720)
        self.window.show()
        self.application.processEvents()
        self.assertEqual(5, self.window.tabs.count())
        self.assertTrue(self.window.tabs.isVisible())
        self.assertTrue(self.window.link_button.isVisible())
        self.window.hide()

    def test_z_injected_fault_is_localized_and_creates_one_demo_ticket(self) -> None:
        self.window._inject()
        for _ in range(75):
            self.window.demo.tick()
        self.window._paint()
        self.assertIn("WS-01", self.window.evidence_status.text())
        self.assertIn("CRITICAL", self.window.evidence_status.text())
        self.assertIn("spindle", _table_text(self.window.subsystem_table))
        self.assertIn("spindle.current_speed_residual", _table_text(self.window.physics_table))
        self.assertEqual(1, self.window.ticket_table.rowCount())
        self.assertEqual("URGENT", self.window.ticket_table.item(0, 0).text())
        self.assertIn("DETERMINISTIC EVIDENCE", self.window.ticket_detail.toPlainText())
        self.assertIn("RETRIEVED / LLM ENRICHMENT", self.window.ticket_detail.toPlainText())


class TrendWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])

    def test_trend_handles_no_one_constant_and_many_samples(self) -> None:
        trend = TelemetryTrend()
        trend.resize(480, 180)
        cases = (
            ((), (), "INSUFFICIENT TREND DATA"),
            ((1.0,), (2.0,), "INSUFFICIENT TREND DATA"),
            ((1.0, 2.0, 3.0), (2.0, 2.0, 2.0), "RAW TELEMETRY WINDOW"),
            ((1.0, 2.0, 3.0, 4.0), (1.0, 3.0, 2.0, 4.0), "RAW TELEMETRY WINDOW"),
        )
        for timestamps, values, message in cases:
            with self.subTest(values=values):
                trend.set_series("channel", "A", timestamps, values)
                self.assertEqual(message, trend.message)
                image = trend.grab()
                self.assertFalse(image.isNull())
        trend.close()


if __name__ == "__main__":
    unittest.main()
