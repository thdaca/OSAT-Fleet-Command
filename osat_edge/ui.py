"""Transparent PyQt6 edge-monitoring HMI for the deterministic research demo."""

from __future__ import annotations

import datetime as dt
import math
import sys
import tempfile
from pathlib import Path
from typing import Iterable, Sequence

from PyQt6.QtCore import QLockFile, QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QColor, QMouseEvent, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import (
    QAbstractItemView,
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
    QScrollArea,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .common import DataOrigin, HealthState, RELEASE_CLASS, RuntimeMode, VERSION
from .demo import DemoFleet, create_demo_fleet
from .machines import STATION_ORDER, STATIONS
from .roadmap.step01_physics_library import (
    PhysicsRelation,
    ResearchCandidate,
    audit_physics_library,
    physics_readiness_report,
    research_catalog_for_family,
)
from .roadmap.step08_live_telemetry import FEATURE_WINDOW
from .roadmap.step09_health_risk import HealthAssessment
from .roadmap.step15_maintenance_ticket import MaintenanceTicket, list_tickets


PALETTE = {
    "background": "#0B0904",
    "panel": "#121006",
    "panel_secondary": "#18130A",
    "amber": "#FFB000",
    "amber_secondary": "#D89A00",
    "amber_muted": "#C08B23",
    "light": "#F4E2B5",
    "watch": "#FFCC00",
    "degraded": "#FF5A36",
    "critical": "#FF2D2D",
    "unknown": "#B8B0A0",
}


QSS = f"""
QWidget {{ background: {PALETTE['background']}; color: {PALETTE['light']};
           font-family: 'Segoe UI'; font-size: 10pt; }}
QMainWindow {{ background: {PALETTE['background']}; }}
QFrame#header, QFrame#demo, QFrame#summary, QFrame#statusStrip {{
    background: {PALETTE['panel']}; border: 1px solid {PALETTE['amber_secondary']};
}}
QLabel#title {{ color: {PALETTE['amber']}; font: 700 20px 'Cascadia Mono', 'Consolas'; }}
QLabel#release {{ color: {PALETTE['amber_muted']}; font: 700 9px 'Cascadia Mono', 'Consolas'; }}
QLabel#section {{ color: {PALETTE['amber']}; font: 700 10px 'Cascadia Mono', 'Consolas'; }}
QLabel#instrument {{ color: {PALETTE['light']}; font-family: 'Cascadia Mono', 'Consolas'; }}
QFrame#machine {{ background: {PALETTE['panel']}; border: 1px solid {PALETTE['amber_secondary']};
                  border-left: 4px solid {PALETTE['amber_secondary']}; }}
QFrame#machine[selected="true"] {{ border-top: 2px solid {PALETTE['amber']}; }}
QFrame#machine[state="watch"] {{ border-left-color: {PALETTE['watch']}; }}
QFrame#machine[state="degraded"] {{ border-left-color: {PALETTE['degraded']}; }}
QFrame#machine[state="critical"] {{ border-left-color: {PALETTE['critical']}; }}
QFrame#machine[state="unknown"] {{ border-left-color: {PALETTE['unknown']}; }}
QLabel#machineTitle {{ color: {PALETTE['amber']}; font: 700 10px 'Cascadia Mono', 'Consolas'; }}
QLabel#health {{ color: {PALETTE['amber_secondary']}; font: 700 15px 'Cascadia Mono', 'Consolas'; }}
QPushButton {{ background: {PALETTE['panel_secondary']}; border: 1px solid {PALETTE['amber_secondary']};
               color: {PALETTE['light']}; padding: 6px 10px; }}
QPushButton:hover, QPushButton:focus {{ border-color: {PALETTE['amber']}; }}
QPushButton#danger {{ color: {PALETTE['degraded']}; border-color: {PALETTE['degraded']}; }}
QComboBox, QPlainTextEdit, QTableWidget {{ background: {PALETTE['panel']};
    border: 1px solid {PALETTE['amber_secondary']}; selection-background-color: #4A350D;
    selection-color: {PALETTE['light']}; }}
QComboBox {{ padding: 5px 8px; }}
QHeaderView::section {{ background: {PALETTE['panel_secondary']}; color: {PALETTE['amber']};
                        padding: 5px; border: 0; border-right: 1px solid #4A350D; }}
QTableWidget {{ gridline-color: #3D2D10; alternate-background-color: #151106; }}
QTabWidget::pane {{ border: 1px solid {PALETTE['amber_secondary']}; }}
QTabBar::tab {{ background: {PALETTE['panel']}; color: {PALETTE['amber_muted']};
                padding: 8px 18px; border: 1px solid #3D2D10; }}
QTabBar::tab:selected {{ background: {PALETTE['panel_secondary']}; color: {PALETTE['amber']};
                         border-bottom: 2px solid {PALETTE['amber']}; }}
QTabBar::tab:focus {{ border: 1px solid {PALETTE['light']}; }}
QCheckBox {{ color: {PALETTE['light']}; }}
QSplitter::handle {{ background: #4A350D; }}
QScrollArea {{ border: 0; }}
"""


HEALTH_COLOR = {
    HealthState.UNKNOWN: PALETTE["unknown"],
    HealthState.NORMAL: PALETTE["amber_secondary"],
    HealthState.WATCH: PALETTE["watch"],
    HealthState.DEGRADED: PALETTE["degraded"],
    HealthState.CRITICAL: PALETTE["critical"],
}


def format_value(value: float | None, *, score: bool = False) -> str:
    """Format display values without implying unsupported numerical precision."""

    if value is None or not math.isfinite(value):
        return "N/A"
    if score:
        return f"{value:.3f}"
    magnitude = abs(value)
    if magnitude >= 1000:
        return f"{value:.0f}"
    if magnitude >= 100:
        return f"{value:.1f}"
    if magnitude >= 1:
        return f"{value:.2f}"
    return f"{value:.3f}"


def format_age(seconds: float | None) -> str:
    if seconds is None or seconds < 0 or not math.isfinite(seconds):
        return "N/A"
    if seconds < 60:
        return f"{seconds:.1f} s"
    minutes, remainder = divmod(int(seconds), 60)
    if minutes < 60:
        return f"{minutes}m {remainder:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m"


def _utc_clock(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).strftime("%H:%M:%S.%f")[:12] + " UTC"


def _words(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw).replace("_", " ")


def _joined(values: Iterable[object], *, empty: str = "NOT AVAILABLE") -> str:
    rendered = [str(getattr(value, "value", value)) for value in values]
    return "\n".join(rendered) if rendered else empty


def _table(columns: Sequence[str], accessible_name: str) -> QTableWidget:
    table = QTableWidget(0, len(columns))
    table.setHorizontalHeaderLabels(list(columns))
    table.setAccessibleName(accessible_name)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    table.setAlternatingRowColors(True)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    table.horizontalHeader().setStretchLastSection(True)
    return table


def _set_row(table: QTableWidget, row: int, values: Sequence[object]) -> None:
    for column, value in enumerate(values):
        item = QTableWidgetItem(str(value))
        table.setItem(row, column, item)


class TelemetryTrend(QWidget):
    """One small raw-data trend; it does not smooth or infer from samples."""

    def __init__(self) -> None:
        super().__init__()
        self.channel = "NOT SELECTED"
        self.unit = ""
        self.timestamps: tuple[float, ...] = ()
        self.values: tuple[float, ...] = ()
        self.message = "INSUFFICIENT TREND DATA"
        self.setAccessibleName("Selected raw telemetry trend")
        self.setMinimumHeight(165)

    def set_series(
        self,
        channel: str,
        unit: str,
        timestamps: Sequence[float],
        values: Sequence[float],
    ) -> None:
        self.channel = channel
        self.unit = unit
        self.timestamps = tuple(float(value) for value in timestamps)
        self.values = tuple(float(value) for value in values)
        self.message = "INSUFFICIENT TREND DATA" if len(self.values) < 2 else "RAW TELEMETRY WINDOW"
        self.update()

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(PALETTE["panel"]))
        painter.setPen(QPen(QColor(PALETTE["amber_secondary"]), 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        painter.setPen(QColor(PALETTE["amber"]))
        painter.drawText(12, 22, f"{self.channel}  [{self.unit or 'N/A'}]")
        if len(self.values) < 2:
            painter.setPen(QColor(PALETTE["unknown"]))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.message)
            return
        low, high = min(self.values), max(self.values)
        current = self.values[-1]
        painter.setPen(QColor(PALETTE["light"]))
        painter.drawText(12, self.height() - 10, f"MIN {format_value(low)}   CURRENT {format_value(current)}   MAX {format_value(high)}")
        plot = QRectF(14, 34, max(self.width() - 28, 1), max(self.height() - 68, 1))
        painter.setPen(QPen(QColor("#4A350D"), 1))
        painter.drawRect(plot)
        t0, t1 = self.timestamps[0], self.timestamps[-1]
        span_t = max(t1 - t0, 1e-9)
        span_y = high - low
        if span_y <= 0:
            points = [QPointF(plot.left() + (stamp - t0) / span_t * plot.width(), plot.center().y()) for stamp in self.timestamps]
        else:
            points = [
                QPointF(
                    plot.left() + (stamp - t0) / span_t * plot.width(),
                    plot.bottom() - (value - low) / span_y * plot.height(),
                )
                for stamp, value in zip(self.timestamps, self.values)
            ]
        painter.setPen(QPen(QColor(PALETTE["amber"]), 2))
        painter.drawPolyline(QPolygonF(points))


class MachineCard(QFrame):
    selected = pyqtSignal(str)
    toggled = pyqtSignal(str, bool)

    def __init__(self, family: str, machine_id: str) -> None:
        super().__init__()
        self.family = family
        station = STATIONS[family]
        self.setObjectName("machine")
        self.setProperty("state", "unknown")
        self.setProperty("selected", "false")
        self.setAccessibleName(f"{station.station_id} {station.name} machine card")
        self.setMinimumHeight(110)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(2)
        top = QHBoxLayout()
        self.title_label = QLabel(f"{station.station_id} · {station.name}")
        self.title_label.setObjectName("machineTitle")
        self.monitor = QCheckBox("MONITOR")
        self.monitor.setChecked(True)
        self.monitor.setAccessibleName(f"Include {station.station_id} in local health assessment")
        self.monitor.setToolTip("Include this machine in local health assessment; this does not control equipment.")
        self.monitor.toggled.connect(lambda enabled: self.toggled.emit(self.family, enabled))
        top.addWidget(self.title_label)
        top.addStretch(1)
        top.addWidget(self.monitor)
        layout.addLayout(top)
        self.machine_id = QLabel(machine_id)
        self.machine_id.setObjectName("instrument")
        self.health = QLabel("UNKNOWN")
        self.health.setObjectName("health")
        self.telemetry = QLabel("DATA QUALITY: NOT AVAILABLE · OBSERVABILITY: NOT AVAILABLE")
        self.age = QLabel("ASSESSMENT AGE: N/A")
        self.age.setObjectName("instrument")
        layout.addWidget(self.machine_id)
        layout.addWidget(self.health)
        layout.addWidget(self.telemetry)
        layout.addWidget(self.age)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", "true" if selected else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def update_assessment(
        self,
        assessment: HealthAssessment | None,
        *,
        monitored: bool,
        connected: bool,
        telemetry_valid: bool | None,
        observable: bool | None,
        assessment_age: float | None,
    ) -> None:
        self.monitor.blockSignals(True)
        self.monitor.setChecked(monitored)
        self.monitor.blockSignals(False)
        if not monitored:
            state, color = "unknown", PALETTE["unknown"]
            self.health.setText("ISOLATED — NOT CURRENTLY ASSESSED")
            self.telemetry.setText("LOCAL ASSESSMENT SCOPE: EXCLUDED")
        elif not connected:
            state, color = "unknown", PALETTE["unknown"]
            last = assessment.health_state.value if assessment else "NONE"
            self.health.setText("DISCONNECTED")
            self.telemetry.setText(f"LAST KNOWN: {last} · NOT CURRENT")
        elif assessment is None:
            state, color = "unknown", PALETTE["unknown"]
            self.health.setText("UNKNOWN")
            self.telemetry.setText("DATA QUALITY: NOT AVAILABLE · OBSERVABILITY: NOT AVAILABLE")
        else:
            state = assessment.health_state.value.lower()
            color = HEALTH_COLOR[assessment.health_state]
            self.health.setText(assessment.health_state.value)
            quality = "VALID" if telemetry_valid else "INVALID"
            coverage = "FULL" if observable else "INSUFFICIENT"
            self.telemetry.setText(f"DATA QUALITY: {quality} · OBSERVABILITY: {coverage}")
        self.health.setStyleSheet(f"color:{color};font:700 15px 'Cascadia Mono','Consolas';")
        self.age.setText(f"ASSESSMENT AGE: {format_age(assessment_age)}")
        self.setProperty("state", state)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.selected.emit(self.family)
        super().mousePressEvent(event)


class FleetCommandWindow(QMainWindow):
    def __init__(self, demo: DemoFleet | None = None) -> None:
        super().__init__()
        self.setWindowTitle(f"OSAT Fleet Command {VERSION} · {RELEASE_CLASS}")
        self.resize(1366, 768)
        self.demo = demo or create_demo_fleet()
        self.pipeline = self.demo.pipeline
        self.cards: dict[str, MachineCard] = {}
        self.selected_family = "wafer_saw"
        self._ticket_revision = -1
        self._tickets: list[MaintenanceTicket] = []
        self._physics_items: list[PhysicsRelation | ResearchCandidate] = []
        self._closed = False
        self._build()
        self.setStyleSheet(QSS)
        self.inference_timer = QTimer(self)
        self.inference_timer.timeout.connect(self._tick)
        self.inference_timer.start(400)
        self.paint_timer = QTimer(self)
        self.paint_timer.timeout.connect(self._paint)
        self.paint_timer.start(300)
        self._select("wafer_saw")

    def closeEvent(self, event: QCloseEvent) -> None:
        self.inference_timer.stop()
        self.paint_timer.stop()
        if not self._closed:
            self.demo.close()
            self._closed = True
        super().closeEvent(event)

    @staticmethod
    def _section(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("section")
        return label

    def _selected_machine(self):
        return self.pipeline.machines[self.selected_family]

    def _build(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)
        root.addWidget(self._header())
        root.addWidget(self._control_strip())
        self.tabs = QTabWidget()
        self.tabs.setAccessibleName("Primary OSAT Fleet Command tabs")
        self.tabs.tabBar().setAccessibleName("FLEET MACHINE PHYSICS MAINTENANCE SYSTEM navigation")
        self.tabs.addTab(self._fleet_tab(), "FLEET")
        self.tabs.addTab(self._machine_tab(), "MACHINE")
        self.tabs.addTab(self._physics_tab(), "PHYSICS")
        self.tabs.addTab(self._maintenance_tab(), "MAINTENANCE")
        self.tabs.addTab(self._system_tab(), "SYSTEM")
        root.addWidget(self.tabs, 1)

    def _header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 6, 10, 6)
        names = QVBoxLayout()
        title = QLabel(f"OSAT FLEET COMMAND  {VERSION}")
        title.setObjectName("title")
        release = QLabel(f"{RELEASE_CLASS} · EDGE MONITORING PROTOTYPE · NOT PRODUCTION QUALIFIED")
        release.setObjectName("release")
        names.addWidget(title)
        names.addWidget(release)
        layout.addLayout(names)
        layout.addStretch(1)
        status = QGridLayout()
        self.connection_label = QLabel("CONNECTION: CONNECTED")
        self.runtime_label = QLabel("RUNTIME: SIMULATION")
        self.origin_label = QLabel("DATA ORIGIN: SYNTHETIC")
        self.clock_label = QLabel("UTC: --:--:--")
        self.authority_label = QLabel("ACTION AUTHORITY: DEMO TICKETS ONLY")
        for label in (self.connection_label, self.runtime_label, self.origin_label, self.clock_label, self.authority_label):
            label.setObjectName("instrument")
        status.addWidget(self.connection_label, 0, 0)
        status.addWidget(self.runtime_label, 0, 1)
        status.addWidget(self.origin_label, 1, 0)
        status.addWidget(self.clock_label, 1, 1)
        status.addWidget(self.authority_label, 2, 0, 1, 2)
        layout.addLayout(status)
        return header

    def _control_strip(self) -> QFrame:
        strip = QFrame()
        strip.setObjectName("statusStrip")
        layout = QHBoxLayout(strip)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.addWidget(self._section("SELECTED MACHINE"))
        self.machine_combo = QComboBox()
        self.machine_combo.setAccessibleName("Selected machine")
        for family in STATION_ORDER:
            station = STATIONS[family]
            self.machine_combo.addItem(f"{station.station_id} · {station.name}", family)
        self.machine_combo.setCurrentIndex(self.machine_combo.findData("wafer_saw"))
        self.machine_combo.currentIndexChanged.connect(self._select_combo)
        layout.addWidget(self.machine_combo)
        self.link_button = QPushButton("DISCONNECT INPUT")
        self.link_button.setAccessibleName("Disconnect telemetry input")
        self.link_button.setToolTip("Pauses local telemetry assessment; it does not control equipment.")
        self.link_button.clicked.connect(self._toggle_link)
        layout.addWidget(self.link_button)
        layout.addStretch(1)
        self.demo_controls = QFrame()
        self.demo_controls.setObjectName("demo")
        demo_layout = QHBoxLayout(self.demo_controls)
        demo_layout.setContentsMargins(7, 2, 7, 2)
        demo_layout.addWidget(self._section("DEMO CONTROLS · SIMULATION ONLY"))
        self.inject_button = QPushButton("INJECT WS-01 SPINDLE FAULT")
        self.inject_button.setObjectName("danger")
        self.inject_button.setAccessibleName("Inject simulated WS-01 spindle fault")
        self.inject_button.clicked.connect(self._inject)
        self.clear_button = QPushButton("CLEAR WS-01 FAULT")
        self.clear_button.setAccessibleName("Clear simulated WS-01 spindle fault")
        self.clear_button.clicked.connect(self._clear)
        demo_layout.addWidget(self.inject_button)
        demo_layout.addWidget(self.clear_button)
        layout.addWidget(self.demo_controls)
        return strip

    def _fleet_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        summary = QFrame()
        summary.setObjectName("summary")
        summary_layout = QHBoxLayout(summary)
        self.summary_labels: dict[str, QLabel] = {}
        for state in ("MONITORED", "NORMAL", "WATCH", "DEGRADED", "CRITICAL", "UNKNOWN"):
            label = QLabel(f"{state} 0")
            label.setObjectName("instrument")
            self.summary_labels[state] = label
            summary_layout.addWidget(label)
        summary_layout.addStretch(1)
        layout.addWidget(summary)
        self.fleet_area = QScrollArea()
        self.fleet_area.setAccessibleName("Nine-machine fleet overview")
        self.fleet_area.setWidgetResizable(True)
        card_host = QWidget()
        grid = QGridLayout(card_host)
        grid.setContentsMargins(2, 2, 2, 2)
        grid.setSpacing(6)
        for index, family in enumerate(STATION_ORDER):
            machine = self.pipeline.machines[family]
            card = MachineCard(family, machine.identity.machine_id)
            card.selected.connect(self._select)
            card.toggled.connect(self.pipeline.set_monitored)
            self.cards[family] = card
            grid.addWidget(card, index // 3, index % 3)
        self.fleet_area.setWidget(card_host)
        layout.addWidget(self.fleet_area, 1)
        note = QLabel("SYNTHETIC DEMONSTRATION DATA · Software-flow evidence only; not evidence of real OSAT failure prediction.")
        note.setObjectName("instrument")
        layout.addWidget(note)
        return widget

    def _machine_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.machine_status = QLabel("WS-01 · NOT AVAILABLE")
        self.machine_status.setObjectName("section")
        self.machine_status.setWordWrap(True)
        layout.addWidget(self.machine_status)
        self.telemetry_summary = QLabel("DATA QUALITY: NOT AVAILABLE · OBSERVABILITY: NOT AVAILABLE")
        self.telemetry_summary.setWordWrap(True)
        layout.addWidget(self.telemetry_summary)
        vertical = QSplitter(Qt.Orientation.Vertical)
        top = QSplitter(Qt.Orientation.Horizontal)
        telemetry_panel = QWidget()
        telemetry_layout = QVBoxLayout(telemetry_panel)
        telemetry_layout.setContentsMargins(0, 0, 4, 0)
        telemetry_layout.addWidget(self._section("LIVE TELEMETRY · APPROVED CANONICAL CHANNELS"))
        self.telemetry_table = _table(
            ("CHANNEL", "SUBSYSTEM", "VALUE", "UNIT", "REQUIRED", "SOURCE ID", "SAMPLE AGE", "STATUS"),
            "Selected machine live telemetry table",
        )
        telemetry_layout.addWidget(self.telemetry_table)
        top.addWidget(telemetry_panel)
        trend_panel = QWidget()
        trend_layout = QVBoxLayout(trend_panel)
        trend_layout.setContentsMargins(4, 0, 0, 0)
        trend_layout.addWidget(self._section("SHORT TREND · RAW DATA"))
        self.trend_selector = QComboBox()
        self.trend_selector.setAccessibleName("Raw telemetry trend channel")
        self.trend_selector.currentIndexChanged.connect(self._update_trend)
        trend_layout.addWidget(self.trend_selector)
        self.trend = TelemetryTrend()
        trend_layout.addWidget(self.trend)
        self.model_status = QPlainTextEdit()
        self.model_status.setReadOnly(True)
        self.model_status.setAccessibleName("Exact-machine and family model status")
        self.model_status.setMaximumHeight(145)
        trend_layout.addWidget(self.model_status)
        top.addWidget(trend_panel)
        top.setSizes([820, 420])
        vertical.addWidget(top)
        evidence_panel = QWidget()
        evidence_layout = QVBoxLayout(evidence_panel)
        evidence_layout.setContentsMargins(0, 4, 0, 0)
        self.evidence_status = QLabel("MODEL / SUBSYSTEM EVIDENCE: NOT AVAILABLE")
        self.evidence_status.setObjectName("section")
        evidence_layout.addWidget(self.evidence_status)
        self.subsystem_table = _table(
            ("SUBSYSTEM", "STATE", "SCORE", "EVIDENCE TYPE", "FEATURE / RELATION", "CURRENT", "HEALTHY REFERENCE", "DEVIATION"),
            "Selected machine subsystem evidence table",
        )
        evidence_layout.addWidget(self.subsystem_table)
        vertical.addWidget(evidence_panel)
        vertical.setSizes([390, 230])
        layout.addWidget(vertical, 1)
        return widget

    def _physics_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        top = QHBoxLayout()
        self.physics_status = QLabel("PHYSICS EVIDENCE: NOT AVAILABLE")
        self.physics_status.setObjectName("section")
        self.physics_audit = QLabel("PHYSICS LIBRARY AUDIT: NOT AVAILABLE")
        self.physics_audit.setObjectName("instrument")
        top.addWidget(self.physics_status)
        top.addStretch(1)
        top.addWidget(self.physics_audit)
        layout.addLayout(top)
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.physics_table = _table(
            ("STATUS", "MATURITY", "RELATION", "SUBSYSTEM", "OUTPUT", "CURRENT", "UNIT", "DOMAIN", "PRIMARY BLOCKER"),
            "Step01 physics research catalog table",
        )
        physics_header = self.physics_table.horizontalHeader()
        for column, width in enumerate((100, 135, 205, 80, 215, 165, 50, 140)):
            physics_header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)
            self.physics_table.setColumnWidth(column, width)
        physics_header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)
        self.physics_table.itemSelectionChanged.connect(self._show_physics_detail)
        splitter.addWidget(self.physics_table)
        self.physics_detail = QPlainTextEdit()
        self.physics_detail.setReadOnly(True)
        self.physics_detail.setAccessibleName("Selected physics relation research detail")
        splitter.addWidget(self.physics_detail)
        splitter.setSizes([260, 340])
        layout.addWidget(splitter, 1)
        return widget

    def _maintenance_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.maintenance_context = QLabel("DOWNSTREAM DETERMINISTIC MAINTENANCE WORKFLOW")
        self.maintenance_context.setObjectName("section")
        layout.addWidget(self.maintenance_context)
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.ticket_table = _table(
            ("PRIORITY", "STATUS", "MACHINE", "HEALTH", "UPDATED UTC", "EXPLANATION BACKEND"),
            "Deterministic maintenance ticket table",
        )
        self.ticket_table.itemSelectionChanged.connect(self._show_ticket)
        splitter.addWidget(self.ticket_table)
        self.ticket_detail = QPlainTextEdit()
        self.ticket_detail.setReadOnly(True)
        self.ticket_detail.setAccessibleName("Selected maintenance ticket detail")
        splitter.addWidget(self.ticket_detail)
        splitter.setSizes([220, 360])
        layout.addWidget(splitter, 1)
        return widget

    def _system_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.system_text = QPlainTextEdit()
        self.system_text.setReadOnly(True)
        self.system_text.setAccessibleName("Runtime security and authority transparency")
        layout.addWidget(self.system_text)
        return widget

    def _tick(self) -> None:
        self.demo.tick()

    def _paint(self) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        self.clock_label.setText(f"UTC: {_utc_clock(now)}")
        machine = self._selected_machine()
        mode = machine.source.runtime_mode
        origin = DataOrigin.SYNTHETIC if mode is RuntimeMode.SIMULATION else DataOrigin.REAL_OSAT
        authority = "DEMO TICKETS ONLY" if mode is RuntimeMode.SIMULATION else "RESEARCH OBSERVE ONLY"
        self.connection_label.setText(f"CONNECTION: {self.pipeline.link_state}")
        self.runtime_label.setText(f"RUNTIME: {mode.value}")
        self.origin_label.setText(f"DATA ORIGIN: {origin.value}")
        self.authority_label.setText(f"ACTION AUTHORITY: {authority}")
        simulation = mode is RuntimeMode.SIMULATION
        self.demo_controls.setVisible(simulation)
        self.inject_button.setEnabled(simulation)
        self.clear_button.setEnabled(simulation)
        for family, item in self.pipeline.machines.items():
            result = item.last_result
            assessment = result.assessment if result is not None else None
            status = result.telemetry_status if result is not None else None
            age = None
            if assessment is not None:
                latest = [item.store.latest(spec.name) for spec in item.station.channels]
                samples = [sample for sample in latest if sample is not None]
                if samples:
                    age = max((assessment.timestamp - max(sample.timestamp for sample in samples)).total_seconds(), 0.0)
            self.cards[family].set_selected(family == self.selected_family)
            self.cards[family].update_assessment(
                assessment,
                monitored=item.monitored,
                connected=self.pipeline.connected,
                telemetry_valid=status.valid if status else None,
                observable=status.observable if status else None,
                assessment_age=age,
            )
        self._refresh_summary()
        self._refresh_machine()
        self._refresh_physics()
        self._refresh_tickets()
        self._refresh_system()

    def _refresh_summary(self) -> None:
        counts = {state.value: 0 for state in HealthState}
        monitored = sum(machine.monitored for machine in self.pipeline.machines.values())
        if self.pipeline.connected:
            for machine in self.pipeline.machines.values():
                if not machine.monitored:
                    continue
                state = machine.last_result.assessment.health_state if machine.last_result else HealthState.UNKNOWN
                counts[state.value] += 1
        else:
            counts[HealthState.UNKNOWN.value] = monitored
        self.summary_labels["MONITORED"].setText(f"MONITORED {monitored}")
        for state in ("NORMAL", "WATCH", "DEGRADED", "CRITICAL", "UNKNOWN"):
            self.summary_labels[state].setText(f"{state} {counts[state]}")
        self.summary_labels["NORMAL"].setStyleSheet(f"color:{PALETTE['amber_secondary']};")
        self.summary_labels["WATCH"].setStyleSheet(f"color:{PALETTE['watch']};")
        self.summary_labels["DEGRADED"].setStyleSheet(f"color:{PALETTE['degraded']};")
        self.summary_labels["CRITICAL"].setStyleSheet(f"color:{PALETTE['critical']};")
        self.summary_labels["UNKNOWN"].setStyleSheet(f"color:{PALETTE['unknown']};")

    def _select_combo(self) -> None:
        family = self.machine_combo.currentData()
        if isinstance(family, str):
            self._select(family)

    def _select(self, family: str) -> None:
        if family not in self.pipeline.machines:
            return
        self.selected_family = family
        index = self.machine_combo.findData(family)
        if index >= 0 and self.machine_combo.currentIndex() != index:
            self.machine_combo.setCurrentIndex(index)
        self._populate_trend_selector()
        self._ticket_revision = -1
        self._paint()

    def _toggle_link(self) -> None:
        connected = not self.pipeline.connected
        self.pipeline.set_connected(connected)
        self.link_button.setText("DISCONNECT INPUT" if connected else "RECONNECT INPUT")
        self.link_button.setAccessibleName("Disconnect telemetry input" if connected else "Reconnect telemetry input")
        self._paint()

    def _inject(self) -> None:
        if self._selected_machine().source.runtime_mode is not RuntimeMode.SIMULATION:
            return
        self.demo.inject_ws_spindle()
        self._select("wafer_saw")

    def _clear(self) -> None:
        if self._selected_machine().source.runtime_mode is RuntimeMode.SIMULATION:
            self.demo.clear_ws_fault()

    def _populate_trend_selector(self) -> None:
        current = self.trend_selector.currentData() if hasattr(self, "trend_selector") else None
        self.trend_selector.blockSignals(True)
        self.trend_selector.clear()
        for channel in self._selected_machine().station.channels:
            self.trend_selector.addItem(f"{channel.name} [{channel.unit}]", channel.name)
        index = self.trend_selector.findData(current)
        self.trend_selector.setCurrentIndex(index if index >= 0 else 0)
        self.trend_selector.blockSignals(False)

    @staticmethod
    def _issue_map(result) -> dict[str, str]:
        if result is None:
            return {}
        issues: dict[str, str] = {}
        for issue in result.telemetry_status.issues:
            name, separator, detail = issue.partition(": ")
            if separator:
                issues[name] = detail.upper()
        return issues

    def _refresh_machine(self) -> None:
        machine = self._selected_machine()
        result = machine.last_result
        assessment = result.assessment if result else None
        station = machine.station
        current_prefix = "" if self.pipeline.connected else "LAST KNOWN ASSESSMENT · "
        if assessment is None:
            self.machine_status.setText(f"{station.station_id} · {station.name} · HEALTH: NOT AVAILABLE")
            self.telemetry_summary.setText("DATA QUALITY: NOT AVAILABLE · OBSERVABILITY: NOT AVAILABLE")
        else:
            self.machine_status.setText(
                f"{current_prefix}{station.station_id} · {station.name} · HEALTH: {assessment.health_state.value} · "
                f"EQUIPMENT STATE: {assessment.equipment_state.value} · LAST ASSESSMENT: {_utc_clock(assessment.timestamp)} · "
                f"RUNTIME: {assessment.runtime_mode.value} · MONITORED: {'YES' if machine.monitored else 'NO'}"
            )
            status = result.telemetry_status
            issues = "; ".join(status.issues) or "NONE"
            freshness = "CURRENT" if self.pipeline.connected else "LAST KNOWN — NOT CURRENT"
            self.telemetry_summary.setText(
                f"DATA QUALITY: {'VALID' if status.valid else 'INVALID'} · "
                f"OBSERVABILITY: {'FULL' if status.observable else 'INSUFFICIENT'} · {freshness} · ISSUES: {issues}"
            )
        issues = self._issue_map(result)
        self.telemetry_table.setRowCount(len(station.channels))
        reference_time = assessment.timestamp if assessment else None
        for row, spec in enumerate(station.channels):
            sample = machine.store.latest(spec.name)
            age = None if sample is None or reference_time is None else max((reference_time - sample.timestamp).total_seconds(), 0.0)
            if not self.pipeline.connected and sample is not None:
                channel_status = "LAST KNOWN"
            elif spec.name in issues:
                channel_status = issues[spec.name]
            elif sample is None:
                channel_status = "MISSING"
            else:
                channel_status = "CURRENT"
            values = (
                spec.name,
                spec.subsystem,
                format_value(sample.value if sample else None),
                spec.unit,
                "REQUIRED" if spec.required else "OPTIONAL",
                spec.source_id,
                format_age(age),
                channel_status,
            )
            _set_row(self.telemetry_table, row, values)
            if sample is not None:
                for column in range(self.telemetry_table.columnCount()):
                    self.telemetry_table.item(row, column).setToolTip(sample.timestamp.isoformat())
        self._update_trend()
        self._refresh_models()
        self._refresh_evidence()

    def _update_trend(self) -> None:
        if not hasattr(self, "trend_selector"):
            return
        machine = self._selected_machine()
        channel_name = self.trend_selector.currentData()
        spec = next((item for item in machine.station.channels if item.name == channel_name), None)
        result = machine.last_result
        if spec is None or result is None:
            self.trend.set_series(str(channel_name or "NOT SELECTED"), spec.unit if spec else "", (), ())
            return
        window = machine.store.window(channel_name, end=result.assessment.timestamp, duration=FEATURE_WINDOW)
        if window is None:
            self.trend.set_series(channel_name, spec.unit, (), ())
        else:
            self.trend.set_series(channel_name, spec.unit, window.timestamps, window.values)

    def _refresh_models(self) -> None:
        machine = self._selected_machine()
        result = machine.last_result
        assessment = result.assessment if result else None
        exact = machine.machine_model
        if exact is None:
            exact_text = "EXACT-MACHINE MODEL\nSTATUS: UNAVAILABLE"
        else:
            context = assessment.equipment_state if assessment else None
            available = context in exact.contexts if context is not None else False
            exact_text = (
                "EXACT-MACHINE MODEL\n"
                f"STATUS: LOADED\nDATA ORIGIN: {exact.origin.value}\nMACHINE IDENTITY: {exact.machine.machine_id}\n"
                f"EQUIPMENT-STATE CONTEXT: {_words(context) if context else 'NOT AVAILABLE'} · {'AVAILABLE' if available else 'UNAVAILABLE'}"
            )
        family = machine.family_model
        if family is None:
            family_text = "FAMILY MODEL\nSTATUS: UNAVAILABLE\nRISK SCORE: NOT AVAILABLE\nUNCALIBRATED — NOT A FAILURE PROBABILITY"
        else:
            risk = assessment.family_risk_score if assessment else None
            family_text = (
                "FAMILY MODEL\n"
                f"STATUS: LOADED\nFAMILY: {family.family}\nDATA ORIGIN: {family.origin.value}\n"
                f"RISK SCORE: {format_value(risk, score=True)}\nUNCALIBRATED — NOT A FAILURE PROBABILITY"
            )
        self.model_status.setPlainText(exact_text + "\n\n" + family_text)

    def _refresh_evidence(self) -> None:
        machine = self._selected_machine()
        result = machine.last_result
        if result is None:
            self.evidence_status.setText("MODEL / SUBSYSTEM EVIDENCE: NOT AVAILABLE")
            self.subsystem_table.setRowCount(0)
            return
        assessment = result.assessment
        prefix = "LAST KNOWN · " if not self.pipeline.connected else ""
        self.evidence_status.setText(
            f"{prefix}{machine.identity.station_id} · HEALTH DECISION: {assessment.health_state.value} · DEVIATIONS ARE EVIDENCE, NOT CAUSAL DIAGNOSES"
        )
        rows: list[tuple[object, ...]] = []
        for subsystem in assessment.subsystem_health:
            if not subsystem.deviations:
                rows.append((subsystem.subsystem, subsystem.state.value, format_value(subsystem.score, score=True), "NOT AVAILABLE", subsystem.reason or "NO CURRENT DEVIATION", "N/A", "N/A", "N/A"))
                continue
            for deviation in sorted(subsystem.deviations, key=lambda item: item.score, reverse=True):
                evidence_type = "PHYSICS RELATION" if deviation.kind == "physics" else "STATISTICAL / PHYSICAL FEATURE"
                rows.append((
                    subsystem.subsystem,
                    subsystem.state.value,
                    format_value(subsystem.score, score=True),
                    evidence_type,
                    deviation.feature,
                    format_value(deviation.value),
                    format_value(deviation.healthy_center),
                    f"{deviation.z_score:+.2f} scales · contribution {deviation.score:.3f}",
                ))
        if assessment.family_risk_score is not None:
            localized = bool(assessment.suspected_subsystems)
            rows.append((
                "MACHINE-WIDE" if not localized else "MACHINE",
                assessment.health_state.value,
                "N/A",
                "FAMILY RISK",
                "SUBSYSTEM NOT LOCALIZED" if not localized else "UNCALIBRATED FAMILY RISK",
                format_value(assessment.family_risk_score, score=True),
                "N/A",
                "UNCALIBRATED — NOT A FAILURE PROBABILITY",
            ))
        self.subsystem_table.setRowCount(len(rows))
        for row, values in enumerate(rows):
            _set_row(self.subsystem_table, row, values)

    def _physics_deviations(self) -> dict[str, object]:
        result = self._selected_machine().last_result
        if result is None:
            return {}
        return {
            deviation.feature: deviation
            for subsystem in result.assessment.subsystem_health
            for deviation in subsystem.deviations
            if deviation.kind == "physics"
        }

    def _refresh_physics(self) -> None:
        machine = self._selected_machine()
        previous_id = None
        row = self.physics_table.currentRow()
        if 0 <= row < len(self._physics_items):
            previous_id = self._item_id(self._physics_items[row])
        self._physics_items = list(research_catalog_for_family(machine.identity.family))
        readiness = {entry.item_id: entry for entry in physics_readiness_report()}
        deviations = self._physics_deviations()
        feature_set = machine.last_result.feature_set if machine.last_result else None
        feature_by_name = feature_set.by_name if feature_set else {}
        self.physics_table.setRowCount(len(self._physics_items))
        for row, item in enumerate(self._physics_items):
            item_id = self._item_id(item)
            entry = readiness.get(item_id)
            if isinstance(item, PhysicsRelation):
                matching = [feature for feature in feature_by_name.values() if feature.relation_id == item.relation_id]
                deviation = next((deviations.get(feature.name) for feature in matching if feature.name in deviations), None)
                current = format_value(deviation.value) if deviation is not None else "N/A — NO CURRENT EVIDENCE"
                domain = "UNKNOWN / NOT VERIFIED"
                output, unit = item.output_name, item.output_unit
            else:
                current, domain, output, unit = "N/A — NOT RUNTIME", "NOT RUNTIME", "N/A", "N/A"
            values = (
                item.status.value,
                item.evidence_maturity.value,
                item_id,
                item.subsystem,
                output,
                current if self.pipeline.connected else f"LAST KNOWN · {current}",
                unit,
                domain,
                entry.major_blocker if entry else item.major_blocker,
            )
            _set_row(self.physics_table, row, values)
        issues = audit_physics_library()
        self.physics_audit.setText("PHYSICS LIBRARY AUDIT: PASS — INTERNAL CONSISTENCY ONLY" if not issues else f"PHYSICS LIBRARY AUDIT: {len(issues)} ISSUES")
        current = "LAST KNOWN PHYSICS EVIDENCE" if not self.pipeline.connected else "CURRENT PHYSICS EVIDENCE"
        self.physics_status.setText(
            f"{machine.identity.station_id} · {current} · {len(self._physics_items)} CATALOG ITEMS · RELATION OUTPUT IS NOT A DIAGNOSIS"
        )
        selected = next((index for index, item in enumerate(self._physics_items) if self._item_id(item) == previous_id), 0)
        if self._physics_items:
            self.physics_table.selectRow(selected)
            self._show_physics_detail()
        else:
            self.physics_detail.setPlainText("NO PHYSICS CATALOG ITEMS — NOT AVAILABLE")

    @staticmethod
    def _item_id(item: PhysicsRelation | ResearchCandidate) -> str:
        return item.relation_id if isinstance(item, PhysicsRelation) else item.candidate_id

    def _show_physics_detail(self) -> None:
        row = self.physics_table.currentRow()
        if not 0 <= row < len(self._physics_items):
            self.physics_detail.setPlainText("NOT AVAILABLE")
            return
        item = self._physics_items[row]
        item_id = self._item_id(item)
        claims = "\n".join(
            f"- {claim.statement} [scope: {claim.evidence_scope}; limits: {claim.limitations}]"
            for claim in item.evidence_claims
        ) or "NOT AVAILABLE"
        measurements = "\n".join(
            f"- {requirement.channel}: {requirement.measurand} [{requirement.required_unit}] · {requirement.status.value} · {requirement.semantics_required}"
            for requirement in item.measurement_requirements
        ) or "NOT AVAILABLE"
        parameters = "\n".join(
            f"- {parameter.name} [{parameter.unit}] · {parameter.source.value} · {parameter.identifiability_notes}"
            for parameter in getattr(item, "parameter_specs", ())
        ) or "NOT AVAILABLE"
        uncertainty = getattr(item, "measurement_uncertainty_sources", getattr(item, "uncertainty_sources", ()))
        discrepancy = item.model_discrepancy_sources
        sensitivities = "\n".join(
            f"- {value.mechanism_or_fault}: {value.expected_direction.value} · {value.evidence_maturity.value} · {value.rationale}"
            for value in item.target_fault_sensitivities
        ) or "NOT AVAILABLE"
        sensor_faults = "\n".join(
            f"- {value.channel}: {value.failure_mode} · {value.effect_on_output} · can mimic degradation: {'YES' if value.can_mimic_degradation else 'NO'}"
            for value in item.sensor_failure_modes
        ) or "NOT AVAILABLE"
        references = "\n".join(
            f"- {reference.key}: {reference.citation} ({reference.publication_year or 'year not available'}) · {reference.identifier} · limits: {reference.scope_limitations}"
            for reference in item.references
        ) or "NOT AVAILABLE"
        equation = item.equation if isinstance(item, PhysicsRelation) else item.proposed_equation
        mechanism = item.mechanism if isinstance(item, PhysicsRelation) else item.proposed_mechanism
        validity = getattr(item, "validity_conditions", ())
        invalidity = getattr(item, "invalidity_conditions", ())
        calibration = getattr(item, "calibration_requirements", ())
        cross = getattr(item, "cross_sensitivities", ())
        confounders = getattr(item, "confounders", ())
        missing = getattr(item, "missing_variables", ())
        output = f"{item.output_name} [{item.output_unit}]" if isinstance(item, PhysicsRelation) else "NOT RUNTIME"
        decision = getattr(item, "decision_reason", "NOT AVAILABLE")
        detail = f"""RELATION ID
{item_id}

STATUS / EVIDENCE MATURITY / KIND
{item.status.value} · {item.evidence_maturity.value} · {item.kind.value}

DESCRIPTION / PROPOSED MECHANISM
{item.description}
{mechanism}

EXACT ENGINEERING CLAIMS
{claims}

EQUATION
{equation}

OUTPUT + UNIT
{output}

REQUIRED MEASUREMENTS / MEASUREMENT-SEMANTIC STATUS
{measurements}

MISSING VARIABLES
{_joined(missing)}

VALIDITY CONDITIONS
{_joined(validity)}

INVALIDITY CONDITIONS
{_joined(invalidity)}

CALIBRATION REQUIREMENTS
{_joined(calibration)}

PARAMETER IDENTIFIABILITY
{parameters}

CALIBRATION / APPLICABILITY ENVELOPE
NOT AVAILABLE IN CURRENT RUNTIME RESULT — UNKNOWN / NOT VERIFIED

MEASUREMENT UNCERTAINTY SOURCES
{_joined(f'- {value.name}: {value.category.value} · {value.description}' for value in uncertainty)}

MODEL DISCREPANCY SOURCES
{_joined(f'- {value.name}: {value.category.value} · {value.description}' for value in discrepancy)}

FAULT SENSITIVITIES
{sensitivities}

CROSS-SENSITIVITIES
{_joined(cross)}

SENSOR-FAULT SENSITIVITIES
{sensor_faults}

CONFOUNDERS
{_joined(confounders)}

FALSIFICATION CRITERIA
{_joined(item.falsification_tests)}

RECALIBRATION TRIGGERS
{_joined(item.recalibration_triggers)}

RESEARCH DECISION REASON
{decision}

MAJOR BLOCKER
{item.major_blocker}

NEXT EXPERIMENT
{item.next_experiment}

SUPPORTING REFERENCES
{references}
"""
        self.physics_detail.setPlainText(detail)

    def _refresh_tickets(self) -> None:
        if self.pipeline.repository.revision != self._ticket_revision:
            self._ticket_revision = self.pipeline.repository.revision
            self._tickets = list_tickets(self.pipeline.repository)
            self.ticket_table.setRowCount(len(self._tickets))
            for row, ticket in enumerate(self._tickets):
                _set_row(self.ticket_table, row, (ticket.priority, ticket.status, ticket.machine_id, ticket.health_state, ticket.updated_utc, ticket.explanation_backend))
        self.maintenance_context.setText(
            f"SELECTED MACHINE: {self._selected_machine().identity.station_id} · "
            f"ACTION AUTHORITY: {'DEMO TICKETS ONLY' if self._selected_machine().source.runtime_mode is RuntimeMode.SIMULATION else 'OBSERVE ONLY'} · "
            "LLM DOES NOT AUTHORIZE TICKET CREATION"
        )
        if self._tickets and self.ticket_table.currentRow() < 0:
            matching = next((index for index, ticket in enumerate(self._tickets) if ticket.machine_id == self._selected_machine().identity.machine_id), 0)
            self.ticket_table.selectRow(matching)
        elif not self._tickets:
            self.ticket_detail.setPlainText("NO MAINTENANCE TICKETS")

    def _show_ticket(self) -> None:
        row = self.ticket_table.currentRow()
        if not 0 <= row < len(self._tickets):
            self.ticket_detail.setPlainText("NOT AVAILABLE")
            return
        ticket = self._tickets[row]
        backend = "DETERMINISTIC FALLBACK" if ticket.explanation_backend == "deterministic-fallback" else ticket.explanation_backend.upper()
        checks = "\n".join(f"{index + 1}. {check}" for index, check in enumerate(ticket.recommended_checks))
        evidence = "\n".join(f"- {item}" for item in ticket.evidence_descriptions)
        self.ticket_detail.setPlainText(
            f"{ticket.ticket_id} · {ticket.priority} · {ticket.status}\n"
            f"{ticket.station_id} / {ticket.machine_id} · HEALTH: {ticket.health_state} · {'DEMO ONLY' if ticket.demo_only else 'OBSERVE ONLY'}\n"
            f"UPDATED: {ticket.updated_utc}\n\n"
            f"DETERMINISTIC EVIDENCE\n{evidence or 'NOT AVAILABLE'}\n\n"
            f"RETRIEVED / LLM ENRICHMENT\nBACKEND: {backend}\nThe enrichment does not diagnose health or authorize this ticket.\n\n"
            f"SUMMARY\n{ticket.summary}\n\nLIKELY ISSUE (NOT CAUSAL PROOF)\n{ticket.likely_issue}\n\nRECOMMENDED CHECKS\n{checks or 'NOT AVAILABLE'}"
        )

    def _refresh_system(self) -> None:
        machine = self._selected_machine()
        result = machine.last_result
        assessment = result.assessment if result else None
        exact_origin = machine.machine_model.origin.value if machine.machine_model else "NOT AVAILABLE"
        family_origin = machine.family_model.origin.value if machine.family_model else "NOT AVAILABLE"
        usable = len(result.telemetry_status.usable_channels) if result else 0
        required = sum(channel.required for channel in machine.station.channels)
        mode = machine.source.runtime_mode
        authority = "DEMO TICKETS ONLY" if mode is RuntimeMode.SIMULATION else "OBSERVE ONLY — NO MAINTENANCE AUTHORITY"
        llm = "CONFIGURED — LOCAL ONLY" if machine.llm_model_path else "NOT CONFIGURED"
        timestamp = assessment.timestamp.isoformat() if assessment else "NOT AVAILABLE"
        self.system_text.setPlainText(f"""SOFTWARE
PRODUCT: OSAT Fleet Command
VERSION: {VERSION}
RELEASE CLASS: {RELEASE_CLASS}
QUALIFICATION: NOT PRODUCTION QUALIFIED

RUNTIME
CONNECTION STATE: {self.pipeline.link_state}
SOURCE TYPE: {type(machine.source).__name__}
RUNTIME MODE: {mode.value}
SELECTED MACHINE: {machine.identity.station_id} / {machine.identity.machine_id}
ASSESSMENT TIMESTAMP: {timestamp}
CURRENTNESS: {'CURRENT' if self.pipeline.connected else 'LAST KNOWN — NOT CURRENT'}

DATA
EXACT-MACHINE MODEL ORIGIN: {exact_origin}
FAMILY-MODEL ORIGIN: {family_origin}
CANONICAL CHANNEL COUNT: {len(machine.station.channels)}
REQUIRED CHANNEL COUNT: {required}
USABLE CHANNEL COUNT: {usable}

TELEMETRY SECURITY
EXPLICIT APPROVED SOURCE-ID TO CANONICAL-CHANNEL MAPPING
UNKNOWN SOURCE IDs ARE REJECTED
UNAPPROVED PROCESS-IP FIELDS ARE REJECTED
CURRENT SOURCE IDs ARE VISIBLE IN THE MACHINE TELEMETRY TABLE

MAINTENANCE AUTHORITY
{authority}
THIS SOFTWARE DOES NOT CONTROL OR SHUT DOWN EQUIPMENT

LLM
STATUS: {llm}
LLM HAS NO HEALTH-DECISION AUTHORITY
LLM DOES NOT AUTHORIZE TICKET CREATION
DETERMINISTIC TICKETS EXIST BEFORE OPTIONAL PROSE ENRICHMENT

NETWORK
RUNTIME NETWORK DEPENDENCY: NONE

PROPRIETARY BOUNDARY
MODEL INTERNAL ALGORITHM / FITTED INTERNALS NOT DISPLAYED.
INPUT TELEMETRY, PHYSICS EVIDENCE, MODEL OUTPUTS, HEALTH STATE, DATA ORIGIN, AND AUTHORITY ARE VISIBLE.

RESEARCH LIMIT
DESIGN INFORMED BY INDUSTRIAL HMI, ALARM-DISPLAY, OT-SECURITY, AND ACCESSIBILITY GUIDANCE.
NO FORMAL CONFORMANCE OR CERTIFICATION IS CLAIMED.
""")


def main(argv: list[str] | None = None) -> int:
    application = QApplication(argv or sys.argv)
    application.setApplicationName(f"OSAT Fleet Command {VERSION}")
    application.setStyleSheet(QSS)
    lock = QLockFile(str(Path(tempfile.gettempdir()) / "osat-fleet-command.instance.lock"))
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
