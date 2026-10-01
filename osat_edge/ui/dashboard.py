"""Transparent PyQt6 edge-monitoring HMI for the deterministic research demo."""

from __future__ import annotations

import datetime as dt
import sys
import tempfile
from pathlib import Path

from PyQt6.QtCore import QLockFile, QTimer
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..roadmap.pre_steps.pre01_common.contracts import RELEASE_CLASS, RuntimeMode, VERSION
from ..roadmap.pre_steps.pre01_common.authority import AuthorityMode
from ..roadmap.post_steps.post01_demo.demo import DemoFleet, create_demo_fleet
from ..roadmap.pre_steps.pre02_machine_registry.registry import STATION_ORDER, STATIONS


from .theme import QSS
from .widgets import section_label, utc_clock
from .screens.fleet import FleetScreen
from .screens.machine import MachineScreen
from .screens.physics import PhysicsScreen
from .screens.maintenance import MaintenanceScreen
from .screens.system import SystemScreen

class SemiGuardWindow(QMainWindow):
    def __init__(self, demo: DemoFleet | None = None) -> None:
        super().__init__()
        self.setWindowTitle(f"OSAT SemiGuard {VERSION} · {RELEASE_CLASS}")
        self.resize(1366, 768)
        self.demo = demo or create_demo_fleet()
        self.pipeline = self.demo.pipeline
        self.selected_family = "wafer_saw"
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

    @property
    def selected_machine(self):
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
        self.tabs.setAccessibleName("Primary OSAT SemiGuard tabs")
        self.tabs.tabBar().setAccessibleName("FLEET MACHINE PHYSICS MAINTENANCE SYSTEM navigation")
        self.fleet_screen = FleetScreen(self)
        self.tabs.addTab(self.fleet_screen, "FLEET")
        self.machine_screen = MachineScreen(self)
        self.tabs.addTab(self.machine_screen, "MACHINE")
        self.physics_screen = PhysicsScreen(self)
        self.tabs.addTab(self.physics_screen, "PHYSICS")
        self.maintenance_screen = MaintenanceScreen(self)
        self.tabs.addTab(self.maintenance_screen, "MAINTENANCE")
        self.system_screen = SystemScreen(self)
        self.tabs.addTab(self.system_screen, "SYSTEM")
        root.addWidget(self.tabs, 1)

    def _header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 6, 10, 6)
        names = QVBoxLayout()
        title = QLabel(f"OSAT SEMIGUARD  {VERSION}")
        title.setObjectName("title")
        release = QLabel(f"{RELEASE_CLASS} · {AuthorityMode.SHADOW.value} · NOT PRODUCTION QUALIFIED")
        release.setObjectName("release")
        names.addWidget(title)
        names.addWidget(release)
        layout.addLayout(names)
        layout.addStretch(1)
        status = QGridLayout()
        self.connection_label = QLabel("CONNECTION: CONNECTED")
        self.runtime_label = QLabel("RUNTIME: SIMULATION")
        self.origin_label = QLabel("DECLARED DATA ORIGIN: SYNTHETIC")
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
        layout.addWidget(section_label("SELECTED MACHINE"))
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
        demo_layout.addWidget(section_label("DEMO CONTROLS · SIMULATION ONLY"))
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

    def _tick(self) -> None:
        self.demo.tick()

    def _paint(self) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        self.clock_label.setText(f"UTC: {utc_clock(now)}")
        machine = self.selected_machine
        mode = machine.source.runtime_mode
        origin = machine.source.origin
        authority = "DEMO TICKETS ONLY" if mode is RuntimeMode.SIMULATION else "RESEARCH OBSERVE ONLY"
        self.connection_label.setText(f"CONNECTION: {self.pipeline.link_state}")
        self.runtime_label.setText(f"RUNTIME: {mode.value}")
        self.origin_label.setText(f"DECLARED DATA ORIGIN: {origin.value}")
        self.authority_label.setText(f"{AuthorityMode.SHADOW.value} · ACTION AUTHORITY: {authority}")
        simulation = mode is RuntimeMode.SIMULATION
        self.demo_controls.setVisible(simulation)
        self.inject_button.setEnabled(simulation)
        self.clear_button.setEnabled(simulation)
        self.fleet_screen.refresh()
        self.machine_screen.refresh()
        self.physics_screen.refresh()
        self.maintenance_screen.refresh()
        self.system_screen.refresh()

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
        self.machine_screen.select_machine()
        self.maintenance_screen._ticket_revision = -1
        self._paint()

    def _toggle_link(self) -> None:
        connected = not self.pipeline.connected
        self.pipeline.set_connected(connected)
        self.link_button.setText("DISCONNECT INPUT" if connected else "RECONNECT INPUT")
        self.link_button.setAccessibleName("Disconnect telemetry input" if connected else "Reconnect telemetry input")
        self._paint()

    def _inject(self) -> None:
        if self.selected_machine.source.runtime_mode is not RuntimeMode.SIMULATION:
            return
        self.demo.inject_ws_spindle()
        self._select("wafer_saw")

    def _clear(self) -> None:
        if self.selected_machine.source.runtime_mode is RuntimeMode.SIMULATION:
            self.demo.clear_ws_fault()


def main(argv: list[str] | None = None) -> int:
    application = QApplication(argv or sys.argv)
    application.setApplicationName(f"OSAT SemiGuard {VERSION}")
    application.setStyleSheet(QSS)
    lock = QLockFile(str(Path(tempfile.gettempdir()) / "osat-fleet-command.instance.lock"))
    lock.setStaleLockTime(5_000)
    if not lock.tryLock(100):
        QMessageBox.warning(None, "OSAT SemiGuard", "The dashboard is already running.")
        return 2
    window = SemiGuardWindow()
    window.show()
    try:
        return application.exec()
    finally:
        window.demo.close()
        lock.unlock()


if __name__ == "__main__":
    raise SystemExit(main())
