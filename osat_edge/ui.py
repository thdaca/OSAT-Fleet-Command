"""Small PyQt6 dashboard for the deterministic student research demo."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from PyQt6.QtCore import QLockFile, QTimer, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QMouseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .common import HealthState, RELEASE_CLASS, VERSION
from .demo import DemoFleet, create_demo_fleet
from .machines import STATION_ORDER, STATIONS
from .roadmap.step09_health_risk import HealthAssessment
from .roadmap.step15_maintenance_ticket import MaintenanceTicket, list_tickets


QSS = """
QWidget { background: #11100d; color: #e8c879; font-family: 'Segoe UI'; }
QMainWindow { background: #0b0a08; }
QFrame#header { background: #17140d; border-bottom: 1px solid #765b22; }
QLabel#title { color: #ffd36a; font: 700 22px 'Consolas'; }
QLabel#release { color: #ff7043; font: 700 11px 'Consolas'; }
QLabel#section { color: #f2bd54; font: 700 12px 'Consolas'; }
QFrame#machine { background: #18150f; border: 1px solid #55451f; border-left: 3px solid #8b6b27; }
QFrame#machine[alert="true"] { border-left: 3px solid #ff4d2e; }
QLabel#machineTitle { color: #ffd36a; font: 700 11px 'Consolas'; }
QLabel#health { color: #bca76f; font: 700 18px 'Consolas'; }
QPushButton { background: #2a2417; border: 1px solid #765b22; padding: 7px 12px; }
QPushButton:hover { background: #3a301d; }
QPushButton#danger { color: #ff8a65; border-color: #a43d28; }
QComboBox, QPlainTextEdit, QTableWidget { background: #17140f; border: 1px solid #55451f; }
QHeaderView::section { background: #241e12; color: #e8c879; padding: 5px; }
QTabWidget::pane { border: 1px solid #55451f; }
QTabBar::tab { background: #18150f; padding: 8px 16px; }
QTabBar::tab:selected { background: #332815; color: #ffd36a; }
QCheckBox { color: #d8b968; }
"""


HEALTH_COLOR = {
    HealthState.UNKNOWN: "#a08c5a",
    HealthState.NORMAL: "#66c987",
    HealthState.WATCH: "#f0bf4f",
    HealthState.DEGRADED: "#ff865c",
    HealthState.CRITICAL: "#ff3d21",
}


class MachineCard(QFrame):
    selected = pyqtSignal(str)
    toggled = pyqtSignal(str, bool)

    def __init__(self, family: str, machine_id: str) -> None:
        super().__init__()
        self.family = family
        station = STATIONS[family]
        self.setObjectName("machine")
        self.setFixedHeight(128)
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        title = QLabel(f"{station.station_id} · {station.name.upper()}")
        title.setObjectName("machineTitle")
        self.monitor = QCheckBox("MONITOR")
        self.monitor.setChecked(True)
        self.monitor.toggled.connect(
            lambda enabled: self.toggled.emit(self.family, enabled)
        )
        top.addWidget(title)
        top.addStretch(1)
        top.addWidget(self.monitor)
        layout.addLayout(top)
        self.machine_id = QLabel(machine_id)
        self.machine_id.setStyleSheet("color:#8f7a49;font-size:9px;")
        self.health = QLabel("UNKNOWN")
        self.health.setObjectName("health")
        self.telemetry = QLabel("WAITING FOR TELEMETRY")
        self.telemetry.setStyleSheet("color:#9d8958;font-size:9px;")
        layout.addWidget(self.machine_id)
        layout.addWidget(self.health)
        layout.addWidget(self.telemetry)

    def update_assessment(
        self,
        assessment: HealthAssessment | None,
        *,
        monitored: bool,
        connected: bool,
    ) -> None:
        self.monitor.blockSignals(True)
        self.monitor.setChecked(monitored)
        self.monitor.blockSignals(False)
        if not monitored:
            self.health.setText("ISOLATED")
            self.health.setStyleSheet("color:#a08c5a;font:700 18px 'Consolas';")
            self.telemetry.setText("TELEMETRY NOT ASSESSED")
            self.setProperty("alert", False)
            self.style().unpolish(self)
            self.style().polish(self)
            return
        if not connected:
            last = assessment.health_state.value if assessment else "NONE"
            self.health.setText("DISCONNECTED")
            self.health.setStyleSheet("color:#a08c5a;font:700 18px 'Consolas';")
            self.telemetry.setText(f"LAST KNOWN: {last}")
            self.setProperty("alert", False)
            self.style().unpolish(self)
            self.style().polish(self)
            return
        if assessment is None:
            self.health.setText("UNKNOWN")
            self.telemetry.setText("WAITING FOR TELEMETRY")
            return
        self.health.setText(assessment.health_state.value)
        self.health.setStyleSheet(
            f"color:{HEALTH_COLOR[assessment.health_state]};font:700 18px 'Consolas';"
        )
        valid = "VALID" if assessment.telemetry_valid else "INVALID"
        observable = "OBSERVABLE" if assessment.observable else "NOT OBSERVABLE"
        self.telemetry.setText(f"TELEMETRY {valid} · {observable}")
        self.setProperty(
            "alert",
            assessment.health_state in {HealthState.DEGRADED, HealthState.CRITICAL},
        )
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.selected.emit(self.family)
        super().mousePressEvent(event)


class FleetCommandWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"OSAT Fleet Command {VERSION} · {RELEASE_CLASS}")
        self.resize(1360, 850)
        self.demo: DemoFleet = create_demo_fleet()
        self.pipeline = self.demo.pipeline
        self.cards: dict[str, MachineCard] = {}
        self.selected_family = "wafer_saw"
        self._ticket_revision = -1
        self._tickets: list[MaintenanceTicket] = []
        self._build()
        self.setStyleSheet(QSS)
        self.inference_timer = QTimer(self)
        self.inference_timer.timeout.connect(self._tick)
        self.inference_timer.start(400)
        self.paint_timer = QTimer(self)
        self.paint_timer.timeout.connect(self._paint)
        self.paint_timer.start(250)
        self._paint()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.inference_timer.stop()
        self.paint_timer.stop()
        self.demo.close()
        super().closeEvent(event)

    @staticmethod
    def _section(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("section")
        return label

    def _build(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        names = QVBoxLayout()
        title = QLabel(f"OSAT FLEET COMMAND {VERSION}")
        title.setObjectName("title")
        release = QLabel(
            f"{RELEASE_CLASS} · STUDENT RESEARCH SOFTWARE · NOT PRODUCTION QUALIFIED"
        )
        release.setObjectName("release")
        names.addWidget(title)
        names.addWidget(release)
        header_layout.addLayout(names)
        header_layout.addStretch(1)
        self.link_label = QLabel("CONNECTED · SYNTHETIC ASYNC TELEMETRY")
        self.link_label.setStyleSheet("color:#66c987;font:700 10px 'Consolas';")
        header_layout.addWidget(self.link_label)
        root.addWidget(header)

        controls = QHBoxLayout()
        controls.addWidget(self._section("DETERMINISTIC RESEARCH DEMO"))
        self.machine_combo = QComboBox()
        for family in STATION_ORDER:
            station = STATIONS[family]
            self.machine_combo.addItem(f"{station.station_id} · {station.name}", family)
        self.machine_combo.setCurrentIndex(self.machine_combo.findData("wafer_saw"))
        self.machine_combo.currentIndexChanged.connect(self._select_combo)
        controls.addWidget(self.machine_combo)
        self.inject_button = QPushButton("INJECT WS-01 SPINDLE FAULT")
        self.inject_button.setObjectName("danger")
        self.inject_button.clicked.connect(self._inject)
        controls.addWidget(self.inject_button)
        self.clear_button = QPushButton("CLEAR WS-01 FAULT")
        self.clear_button.clicked.connect(self._clear)
        controls.addWidget(self.clear_button)
        self.link_button = QPushButton("DISCONNECT")
        self.link_button.clicked.connect(self._toggle_link)
        controls.addWidget(self.link_button)
        controls.addStretch(1)
        root.addLayout(controls)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._fleet_tab(), "FLEET")
        self.tabs.addTab(self._evidence_tab(), "SUBSYSTEM EVIDENCE")
        self.tabs.addTab(self._ticket_tab(), "MAINTENANCE TICKETS")
        root.addWidget(self.tabs)

    def _fleet_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        grid = QGridLayout()
        for index, family in enumerate(STATION_ORDER):
            machine = self.pipeline.machines[family]
            card = MachineCard(family, machine.identity.machine_id)
            card.selected.connect(self._select)
            card.toggled.connect(self.pipeline.set_monitored)
            self.cards[family] = card
            grid.addWidget(card, index // 3, index % 3)
        layout.addLayout(grid)
        note = QPlainTextEdit()
        note.setReadOnly(True)
        note.setMaximumHeight(70)
        note.setPlainText(
            "Synthetic telemetry is deterministic test infrastructure, not evidence "
            "of real OSAT failure prediction. WS-01 injection demonstrates software flow only."
        )
        layout.addWidget(note)
        return widget

    def _evidence_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.evidence_status = QLabel("UNKNOWN")
        self.evidence_status.setObjectName("section")
        layout.addWidget(self.evidence_status)
        self.subsystem_table = QTableWidget(0, 4)
        self.subsystem_table.setHorizontalHeaderLabels(
            ["SUBSYSTEM", "STATE", "SCORE", "CONTRIBUTING EVIDENCE"]
        )
        self.subsystem_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.subsystem_table)
        return widget

    def _ticket_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.ticket_table = QTableWidget(0, 5)
        self.ticket_table.setHorizontalHeaderLabels(
            ["PRIORITY", "TICKET", "MACHINE", "HEALTH", "EXPLANATION"]
        )
        self.ticket_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.ticket_table.itemSelectionChanged.connect(self._show_ticket)
        layout.addWidget(self.ticket_table)
        self.ticket_detail = QPlainTextEdit()
        self.ticket_detail.setReadOnly(True)
        layout.addWidget(self.ticket_detail)
        return widget

    def _tick(self) -> None:
        self.demo.tick()

    def _paint(self) -> None:
        for family, machine in self.pipeline.machines.items():
            assessment = (
                machine.last_result.assessment if machine.last_result is not None else None
            )
            self.cards[family].update_assessment(
                assessment,
                monitored=machine.monitored,
                connected=self.pipeline.connected,
            )
        self._refresh_evidence()
        self._refresh_tickets()

    def _select_combo(self) -> None:
        family = self.machine_combo.currentData()
        if isinstance(family, str):
            self.selected_family = family
            self._refresh_evidence()

    def _select(self, family: str) -> None:
        self.selected_family = family
        self.machine_combo.setCurrentIndex(self.machine_combo.findData(family))
        self._refresh_evidence()

    def _toggle_link(self) -> None:
        self.pipeline.set_connected(not self.pipeline.connected)
        self.link_button.setText("DISCONNECT" if self.pipeline.connected else "RECONNECT")
        self.link_label.setText(
            "CONNECTED · SYNTHETIC ASYNC TELEMETRY"
            if self.pipeline.connected
            else "DISCONNECTED · INPUT NOT ASSESSED"
        )
        self._paint()

    def _inject(self) -> None:
        self.demo.inject_ws_spindle()
        self._select("wafer_saw")

    def _clear(self) -> None:
        self.demo.clear_ws_fault()

    def _refresh_evidence(self) -> None:
        machine = self.pipeline.machines[self.selected_family]
        result = machine.last_result
        if result is None:
            return
        assessment = result.assessment
        prefix = "LAST KNOWN · " if not self.pipeline.connected else ""
        self.evidence_status.setText(
            f"{prefix}{machine.identity.station_id} · {assessment.health_state.value} · "
            f"TELEMETRY {'VALID' if assessment.telemetry_valid else 'INVALID'}"
        )
        self.subsystem_table.setRowCount(len(assessment.subsystem_health))
        for row, subsystem in enumerate(assessment.subsystem_health):
            ranked = sorted(subsystem.deviations, key=lambda item: item.score, reverse=True)
            evidence = "; ".join(
                f"{item.feature} ({abs(item.z_score):.2f} scales)"
                for item in ranked[:3]
            )
            values = (
                subsystem.subsystem,
                subsystem.state.value,
                "N/A" if subsystem.score is None else f"{subsystem.score:.3f}",
                evidence or subsystem.reason or "",
            )
            for column, value in enumerate(values):
                self.subsystem_table.setItem(row, column, QTableWidgetItem(value))

    def _refresh_tickets(self) -> None:
        if self.pipeline.repository.revision == self._ticket_revision:
            return
        self._ticket_revision = self.pipeline.repository.revision
        self._tickets = list_tickets(self.pipeline.repository)
        self.ticket_table.setRowCount(len(self._tickets))
        for row, ticket in enumerate(self._tickets):
            values = (
                ticket.priority,
                ticket.ticket_id,
                ticket.machine_id,
                ticket.health_state,
                ticket.explanation_backend,
            )
            for column, value in enumerate(values):
                self.ticket_table.setItem(row, column, QTableWidgetItem(value))
        if self._tickets and self.ticket_table.currentRow() < 0:
            self.ticket_table.selectRow(0)

    def _show_ticket(self) -> None:
        row = self.ticket_table.currentRow()
        if not 0 <= row < len(self._tickets):
            return
        ticket = self._tickets[row]
        self.ticket_detail.setPlainText(
            f"{ticket.priority} · {ticket.status} · {ticket.ticket_id}\n"
            f"{ticket.machine_id} · {ticket.health_state} · DEMO ONLY\n\n"
            f"{ticket.summary}\n{ticket.likely_issue}\n\n"
            + "\n".join(
                f"{index + 1}. {check}"
                for index, check in enumerate(ticket.recommended_checks)
            )
            + "\n\nDETERMINISTIC EVIDENCE\n"
            + "\n".join(ticket.evidence_descriptions)
        )


def main(argv: list[str] | None = None) -> int:
    application = QApplication(argv or sys.argv)
    application.setApplicationName(f"OSAT Fleet Command {VERSION}")
    application.setStyleSheet(QSS)
    lock = QLockFile(
        str(Path(tempfile.gettempdir()) / "osat-fleet-command-020.instance.lock")
    )
    lock.setStaleLockTime(5_000)
    if not lock.tryLock(100):
        QMessageBox.warning(None, "OSAT Fleet Command", "The dashboard is already running.")
        return 2
    window = FleetCommandWindow()
    window.show()
    try:
        return application.exec()
    finally:
        window.demo.close()
        lock.unlock()


if __name__ == "__main__":
    raise SystemExit(main())
