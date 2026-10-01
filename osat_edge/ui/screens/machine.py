"""MACHINE screen: presentation only; health and authority are decided by the pipeline."""

from __future__ import annotations


from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QComboBox, QLabel, QPlainTextEdit, QSplitter, QVBoxLayout, QWidget

from ...roadmap.steps.step08_live_telemetry.store import FEATURE_WINDOW


from ..widgets import (
    format_value,
    format_age,
    utc_clock,
    words,
    make_table,
    set_row,
    section_label,
    TelemetryTrend,
)

class MachineScreen(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        layout = QVBoxLayout(self)
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
        telemetry_layout.addWidget(section_label("LIVE TELEMETRY · APPROVED CANONICAL CHANNELS"))
        self.telemetry_table = make_table(
            ("CHANNEL", "SUBSYSTEM", "VALUE", "UNIT", "REQUIRED", "CANONICAL SOURCE ID", "SAMPLE LAG", "STATUS"),
            "Selected machine live telemetry table",
        )
        telemetry_layout.addWidget(self.telemetry_table)
        top.addWidget(telemetry_panel)
        trend_panel = QWidget()
        trend_layout = QVBoxLayout(trend_panel)
        trend_layout.setContentsMargins(4, 0, 0, 0)
        trend_layout.addWidget(section_label("SHORT TREND · RAW DATA"))
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
        self.subsystem_table = make_table(
            ("SUBSYSTEM", "STATE", "SCORE", "EVIDENCE TYPE", "FEATURE / RELATION", "CURRENT", "HEALTHY REFERENCE", "DEVIATION"),
            "Selected machine subsystem evidence table",
        )
        evidence_layout.addWidget(self.subsystem_table)
        vertical.addWidget(evidence_panel)
        vertical.setSizes([390, 230])
        layout.addWidget(vertical, 1)

    def select_machine(self) -> None:
        current = self.trend_selector.currentData() if hasattr(self, "trend_selector") else None
        self.trend_selector.blockSignals(True)
        self.trend_selector.clear()
        for channel in self.window.selected_machine.station.channels:
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

    def refresh(self) -> None:
        machine = self.window.selected_machine
        result = machine.last_result
        assessment = result.assessment if result else None
        station = machine.station
        current_prefix = "" if self.window.pipeline.connected else "LAST KNOWN ASSESSMENT · "
        if assessment is None:
            self.machine_status.setText(f"{station.station_id} · {station.name} · HEALTH: NOT AVAILABLE")
            self.telemetry_summary.setText("DATA QUALITY: NOT AVAILABLE · OBSERVABILITY: NOT AVAILABLE")
        else:
            self.machine_status.setText(
                f"{current_prefix}{station.station_id} · {station.name} · HEALTH: {assessment.health_state.value} · "
                f"EQUIPMENT STATE: {assessment.equipment_state.value} · LAST ASSESSMENT: {utc_clock(assessment.timestamp)} · "
                f"RUNTIME: {assessment.runtime_mode.value} · MONITORED: {'YES' if machine.monitored else 'NO'}"
            )
            status = result.telemetry_status
            issues = "; ".join(status.issues) or "NONE"
            freshness = "CURRENT" if self.window.pipeline.connected else "LAST KNOWN — NOT CURRENT"
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
            if not self.window.pipeline.connected and sample is not None:
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
            set_row(self.telemetry_table, row, values)
            if sample is not None:
                for column in range(self.telemetry_table.columnCount()):
                    self.telemetry_table.item(row, column).setToolTip(sample.timestamp.isoformat())
        self._update_trend()
        self._refresh_models()
        self._refresh_evidence()

    def _update_trend(self) -> None:
        if not hasattr(self, "trend_selector"):
            return
        machine = self.window.selected_machine
        channel_name = self.trend_selector.currentData()
        spec = next((item for item in machine.station.channels if item.name == channel_name), None)
        result = machine.last_result
        display_channel = str(channel_name or "NOT SELECTED")
        if not self.window.pipeline.connected:
            display_channel = f"LAST KNOWN · {display_channel}"
        if spec is None or result is None:
            self.trend.set_series(display_channel, spec.unit if spec else "", (), ())
            return
        window = machine.store.window(channel_name, end=result.assessment.timestamp, duration=FEATURE_WINDOW)
        if window is None:
            self.trend.set_series(display_channel, spec.unit, (), ())
        else:
            self.trend.set_series(display_channel, spec.unit, window.timestamps, window.values)

    def _refresh_models(self) -> None:
        machine = self.window.selected_machine
        result = machine.last_result
        assessment = result.assessment if result else None
        exact = machine.machine_model
        if exact is None:
            exact_text = "EXACT-MACHINE MODEL\nSTATUS: UNAVAILABLE"
        else:
            context = assessment.equipment_state if assessment else None
            available = context in exact.contexts if context is not None else False
            context_label = (
                "EQUIPMENT-STATE CONTEXT"
                if self.window.pipeline.connected
                else "LAST KNOWN EQUIPMENT-STATE CONTEXT"
            )
            exact_text = (
                "EXACT-MACHINE MODEL\n"
                f"STATUS: LOADED\nDATA ORIGIN: {exact.origin.value}\nMACHINE IDENTITY: {exact.machine.machine_id}\n"
                f"{context_label}: {words(context) if context else 'NOT AVAILABLE'} · {'AVAILABLE' if available else 'UNAVAILABLE'}"
            )
        family = machine.family_model
        if family is None:
            family_text = "FAMILY MODEL\nSTATUS: UNAVAILABLE\nRISK SCORE: NOT AVAILABLE\nUNCALIBRATED — NOT A FAILURE PROBABILITY"
        else:
            risk = assessment.family_risk_score if assessment else None
            risk_label = "RISK SCORE" if self.window.pipeline.connected else "LAST KNOWN RISK SCORE"
            family_text = (
                "FAMILY MODEL\n"
                f"STATUS: LOADED\nFAMILY: {family.family}\nDATA ORIGIN: {family.origin.value}\n"
                f"{risk_label}: {format_value(risk, score=True)}\nUNCALIBRATED — NOT A FAILURE PROBABILITY"
            )
        self.model_status.setPlainText(exact_text + "\n\n" + family_text)

    def _refresh_evidence(self) -> None:
        machine = self.window.selected_machine
        result = machine.last_result
        if result is None:
            self.evidence_status.setText("MODEL / SUBSYSTEM EVIDENCE: NOT AVAILABLE")
            self.subsystem_table.setRowCount(0)
            return
        assessment = result.assessment
        prefix = "LAST KNOWN · " if not self.window.pipeline.connected else ""
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
            set_row(self.subsystem_table, row, values)
