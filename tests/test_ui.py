from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from osat_edge.ui import FleetCommandWindow


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

    def test_ui_has_nine_cards_and_research_header(self) -> None:
        self.assertEqual(9, len(self.window.cards))
        self.assertIn("0.2.0", self.window.windowTitle())
        self.assertIn("RESEARCH / DEVELOPMENT", self.window.windowTitle())

    def test_disconnect_marks_health_as_last_known_not_current(self) -> None:
        self.window._toggle_link()
        card = self.window.cards["wafer_saw"]
        self.assertEqual("DISCONNECTED", card.health.text())
        self.assertIn("LAST KNOWN:", card.telemetry.text())
        self.window._toggle_link()

    def test_monitor_control_isolates_only_one_card(self) -> None:
        card = self.window.cards["wire_bond"]
        card.monitor.setChecked(False)
        self.window._paint()
        self.assertFalse(self.window.pipeline.machines["wire_bond"].monitored)
        self.assertEqual("ISOLATED", card.health.text())
        self.assertTrue(self.window.pipeline.machines["wafer_saw"].monitored)
        card.monitor.setChecked(True)

    def test_injected_fault_appears_in_evidence_and_ticket_views(self) -> None:
        self.window._inject()
        for _ in range(75):
            self.window.demo.tick()
        self.window._paint()
        self.assertIn("CRITICAL", self.window.evidence_status.text())
        self.assertGreater(self.window.subsystem_table.rowCount(), 0)
        self.assertEqual(1, self.window.ticket_table.rowCount())
        self.assertEqual("URGENT", self.window.ticket_table.item(0, 0).text())


if __name__ == "__main__":
    unittest.main()

