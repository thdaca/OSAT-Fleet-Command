"""MAINTENANCE screen: presentation only; health and authority are decided by the pipeline."""

from __future__ import annotations


from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QPlainTextEdit, QSplitter, QVBoxLayout, QWidget

from ...roadmap.pre_steps.pre01_common.contracts import RuntimeMode
from ...roadmap.steps.step15_maintenance_ticket.tickets import MaintenanceTicket, list_tickets


from ..widgets import make_table, set_row

class MaintenanceScreen(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self._ticket_revision = -1
        self._tickets: list[MaintenanceTicket] = []
        layout = QVBoxLayout(self)
        self.maintenance_context = QLabel("DOWNSTREAM DETERMINISTIC MAINTENANCE WORKFLOW")
        self.maintenance_context.setObjectName("section")
        layout.addWidget(self.maintenance_context)
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.ticket_table = make_table(
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

    def refresh(self) -> None:
        rebuilt = self.window.pipeline.repository.revision != self._ticket_revision
        if rebuilt:
            self._ticket_revision = self.window.pipeline.repository.revision
            self._tickets = list_tickets(self.window.pipeline.repository)
            self.ticket_table.blockSignals(True)
            self.ticket_table.setRowCount(len(self._tickets))
            for row, ticket in enumerate(self._tickets):
                set_row(self.ticket_table, row, (ticket.priority, ticket.status, ticket.machine_id, ticket.health_state, ticket.updated_utc, ticket.explanation_backend))
            self.ticket_table.blockSignals(False)
        self.maintenance_context.setText(
            f"SELECTED MACHINE: {self.window.selected_machine.identity.station_id} · "
            f"ACTION AUTHORITY: {'DEMO TICKETS ONLY' if self.window.selected_machine.source.runtime_mode is RuntimeMode.SIMULATION else 'OBSERVE ONLY'} · "
            "LLM DOES NOT AUTHORIZE TICKET CREATION"
        )
        selected_machine_id = self.window.selected_machine.identity.machine_id
        matching = [
            index for index, ticket in enumerate(self._tickets)
            if ticket.machine_id == selected_machine_id
        ]
        current = self.ticket_table.currentRow()
        current_matches = (
            0 <= current < len(self._tickets)
            and self._tickets[current].machine_id == selected_machine_id
        )
        if matching:
            if rebuilt or not current_matches:
                self.ticket_table.selectRow(matching[0])
        else:
            self.ticket_table.clearSelection()
            self.ticket_table.setCurrentCell(-1, -1)
            self.ticket_detail.setPlainText("NO MAINTENANCE TICKETS FOR SELECTED MACHINE")

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
