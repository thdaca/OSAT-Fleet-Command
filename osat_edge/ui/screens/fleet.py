"""FLEET screen: presentation only; health and authority are decided by the pipeline."""

from __future__ import annotations


from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ...roadmap.pre_steps.pre01_common.contracts import HealthState
from ...roadmap.pre_steps.pre02_machine_registry.registry import STATION_ORDER


from ..theme import PALETTE
from ..widgets import MachineCard

class FleetScreen(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.cards: dict[str, MachineCard] = {}
        layout = QVBoxLayout(self)
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
            machine = self.window.pipeline.machines[family]
            card = MachineCard(family, machine.identity.machine_id)
            card.selected.connect(self.window._select)
            card.toggled.connect(self.window.pipeline.set_monitored)
            self.cards[family] = card
            grid.addWidget(card, index // 3, index % 3)
        self.fleet_area.setWidget(card_host)
        layout.addWidget(self.fleet_area, 1)
        note = QLabel("SYNTHETIC DEMONSTRATION DATA · Software-flow evidence only; not evidence of real OSAT failure prediction.")
        note.setObjectName("instrument")
        layout.addWidget(note)

    def refresh(self) -> None:
        for family, item in self.window.pipeline.machines.items():
            result = item.last_result
            assessment = result.assessment if result is not None else None
            status = result.telemetry_status if result is not None else None
            age = None
            if assessment is not None:
                latest = [item.store.latest(spec.name) for spec in item.station.channels]
                samples = [sample for sample in latest if sample is not None]
                if samples:
                    age = max((assessment.timestamp - max(sample.timestamp for sample in samples)).total_seconds(), 0.0)
            self.cards[family].set_selected(family == self.window.selected_family)
            self.cards[family].update_assessment(
                assessment,
                monitored=item.monitored,
                connected=self.window.pipeline.connected,
                telemetry_valid=status.valid if status else None,
                observable=status.observable if status else None,
                assessment_age=age,
            )
        self._refresh_summary()

    def _refresh_summary(self) -> None:
        counts = {state.value: 0 for state in HealthState}
        monitored = sum(machine.monitored for machine in self.window.pipeline.machines.values())
        if self.window.pipeline.connected:
            for machine in self.window.pipeline.machines.values():
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
