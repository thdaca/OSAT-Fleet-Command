"""Transparent PyQt6 edge-monitoring HMI for the deterministic research demo."""

from __future__ import annotations

import datetime as dt
import math
from typing import Iterable, Sequence

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..roadmap.pre_steps.pre02_machine_registry.registry import STATIONS
from ..roadmap.steps.step09_health_risk.health import HealthAssessment


from .theme import PALETTE, HEALTH_COLOR

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


def utc_clock(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).strftime("%H:%M:%S.%f")[:12] + " UTC"


def words(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw).replace("_", " ")


def joined(values: Iterable[object], *, empty: str = "NOT AVAILABLE") -> str:
    rendered = [str(getattr(value, "value", value)) for value in values]
    return "\n".join(rendered) if rendered else empty


def make_table(columns: Sequence[str], accessible_name: str) -> QTableWidget:
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


def set_row(table: QTableWidget, row: int, values: Sequence[object]) -> None:
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
        self.age = QLabel("SAMPLE LAG TO ASSESSMENT: N/A")
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
        self.age.setText(f"SAMPLE LAG TO ASSESSMENT: {format_age(assessment_age)}")
        self.setProperty("state", state)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.selected.emit(self.family)
        super().mousePressEvent(event)


def section_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("section")
    return label
