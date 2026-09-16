"""Deterministic synthetic construction and WS-01 demo fault injection."""

from __future__ import annotations

import datetime as dt
import hashlib
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from ...pre_steps.pre01_common.pre01_common import (
    DataOrigin,
    EquipmentState,
    MachineIdentity,
    OperatingContext,
    RuntimeMode,
    TelemetrySample,
    RELEASE_CLASS,
    VERSION,
)
from ...pre_steps.pre02_machine_registry.pre02_machine_registry import STATIONS, StationDefinition
from ....pipeline import FleetPipeline, MachinePipeline, PipelineResult
from ...steps.step01_physics_library.step01_physics_library import relations_for_family
from ...steps.step02_physical_features.step02_physical_features import FeatureSet, extract_physical_features
from ...steps.step03_physical_residuals.step03_physical_residuals import (
    calculate_physical_residuals,
    fit_relation_parameters,
)
from ...steps.step06_machine_history.step06_machine_history import HealthyInterval, MachineHistory
from ...steps.step07_machine_model.step07_machine_model import MachineModel, fit_machine_model
from ...steps.step08_live_telemetry.step08_live_telemetry import (
    FEATURE_WINDOW,
    BoundedTelemetryStore,
    TelemetryBatch,
    assess_telemetry,
)
from ...steps.step11a_maintenance_db.step11a_maintenance_db import MaintenanceRepository
from ...steps.step11b_oem_manuals.step11b_oem_manuals import DEFAULT_MANUALS_PATH, load_oem_manuals
from ...steps.step15_maintenance_ticket.step15_maintenance_ticket import list_tickets


DEMO_START = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)


def _stable_center(channel: str, unit: str) -> float:
    ranges = {
        "RPM": (20_000.0, 50_000.0), "A": (1.0, 8.0), "mA": (50.0, 250.0),
        "°C": (25.0, 160.0), "kPa": (-75.0, -35.0), "MPa": (0.2, 0.5),
        "bar": (20.0, 100.0), "L/min": (1.0, 5.0), "mm/s": (0.5, 3.0),
        "g": (0.05, 0.4), "µm": (1.0, 20.0), "µrad": (5.0, 30.0),
        "mm": (0.05, 1.0), "N": (2.0, 20.0), "kN": (2.0, 15.0),
        "gf": (20.0, 80.0), "Hz": (-20.0, 20.0), "W": (5.0, 20.0),
        "mV": (5.0, 40.0), "ms": (5.0, 100.0),
    }
    low, high = ranges.get(unit, (1.0, 10.0))
    digest = hashlib.sha256(channel.encode("utf-8")).digest()
    fraction = int.from_bytes(digest[:8], "big") / float(2**64 - 1)
    return low + fraction * (high - low)


class SyntheticTelemetrySource:
    runtime_mode = RuntimeMode.SIMULATION
    origin = DataOrigin.SYNTHETIC

    def __init__(
        self,
        identity: MachineIdentity,
        profile: StationDefinition,
        *,
        started_at: dt.datetime = DEMO_START,
    ) -> None:
        self.identity = identity
        self.profile = profile
        self.started_at = started_at
        self.elapsed = 0.0
        self.next_due = {channel.name: 0.0 for channel in profile.channels}
        self.centers = {
            channel.name: _stable_center(channel.name, channel.unit)
            for channel in profile.channels
        }
        self.injected_subsystem: str | None = None
        self.injection_elapsed = 0.0
        self.injection_strength = 0.0

    def inject_fault(self, subsystem: str, *, strength: float = 1.0) -> None:
        if subsystem not in self.profile.subsystems:
            raise ValueError(f"Unknown demo subsystem {subsystem!r}")
        self.injected_subsystem = subsystem
        self.injection_elapsed = 0.0
        self.injection_strength = float(np.clip(strength, 0.0, 2.0))

    def clear_fault(self) -> None:
        self.injected_subsystem = None
        self.injection_elapsed = 0.0
        self.injection_strength = 0.0

    def _value(self, channel_name: str, subsystem: str, sample_time: float) -> float:
        center = self.centers[channel_name]
        amplitude = max(abs(center) * 0.002, 0.002)
        value = center + amplitude * np.sin(sample_time / 11.0)
        if channel_name == "spindle_speed":
            value = center + amplitude * np.sin(sample_time / 13.0)
        if channel_name == "spindle_current" and "spindle_speed" in self.centers:
            speed_center = self.centers["spindle_speed"]
            speed = speed_center + speed_center * 0.002 * np.sin(sample_time / 13.0)
            value = center + 0.00004 * (speed - speed_center)
        if subsystem == self.injected_subsystem:
            progress = min(self.injection_elapsed / 18.0, 1.0)
            direction = 1.0 if center >= 0 else -1.0
            if self.profile.family == "wafer_saw" and subsystem == "spindle":
                if channel_name == "spindle_current":
                    value += max(abs(center) * 0.9, amplitude * 80.0) * self.injection_strength * progress
                elif channel_name == "spindle_vibration":
                    value += max(abs(center) * 0.25, amplitude * 20.0) * self.injection_strength * progress
            else:
                value += direction * max(abs(center) * 0.9, amplitude * 80.0) * self.injection_strength * progress
        return float(value)

    def poll(self) -> TelemetryBatch:
        self.elapsed += 1.0
        if self.injected_subsystem is not None:
            self.injection_elapsed += 1.0
        samples: list[TelemetrySample] = []
        for channel in self.profile.channels:
            while self.next_due[channel.name] <= self.elapsed:
                sample_time = self.next_due[channel.name]
                samples.append(
                    TelemetrySample(
                        machine_id=self.identity.machine_id,
                        channel=channel.name,
                        timestamp=self.started_at + dt.timedelta(seconds=sample_time),
                        value=self._value(channel.name, channel.subsystem, sample_time),
                        unit=channel.unit,
                        source_id=channel.source_id,
                    )
                )
                self.next_due[channel.name] += channel.period_seconds
        context = OperatingContext(
            machine_id=self.identity.machine_id,
            timestamp=self.started_at + dt.timedelta(seconds=self.elapsed),
            equipment_state=EquipmentState.PROCESSING,
        )
        return TelemetryBatch(tuple(samples), context)


def _demo_identity(station: StationDefinition) -> MachineIdentity:
    return MachineIdentity(
        machine_id=f"DEMO-{station.station_id}",
        family=station.family,
        station_id=station.station_id,
        name=station.name,
    )


def _fit_demo_model(identity: MachineIdentity, station: StationDefinition) -> MachineModel:
    source = SyntheticTelemetrySource(identity, station)
    store = BoundedTelemetryStore(identity, station)
    for _ in range(130):
        store.append_batch(source.poll())
    now = store.latest_context().timestamp  # type: ignore[union-attr]
    windows = store.windows([channel.name for channel in station.channels], end=now)
    parameters: dict[str, dict[str, float]] = {}
    for relation in relations_for_family(station.family):
        if relation.fit is not None:
            parameters[relation.relation_id] = fit_relation_parameters(
                station.family, relation.relation_id, windows
            )
    feature_sets: list[FeatureSet] = []
    for _ in range(35):
        batch = source.poll()
        store.append_batch(batch)
        now = batch.context.timestamp  # type: ignore[union-attr]
        windows = store.windows([channel.name for channel in station.channels], end=now)
        status = assess_telemetry(store, now=now, windows=windows)
        features = extract_physical_features(
            identity,
            station,
            {name: window for name, window in windows.items() if name in status.usable_channels},
            timestamp=now,
            equipment_state=EquipmentState.PROCESSING,
            window_start=now - FEATURE_WINDOW,
        )
        residuals = calculate_physical_residuals(
            station.family, windows, fitted_parameters=parameters
        )
        feature_sets.append(replace(features, features=features.features + residuals))
    history = MachineHistory(
        machine=identity,
        origin=DataOrigin.SYNTHETIC,
        feature_sets=tuple(feature_sets),
        confirmed_healthy=(
            HealthyInterval(
                identity.machine_id,
                DEMO_START,
                max(feature.window_end for feature in feature_sets),
            ),
        ),
    )
    return fit_machine_model(
        history,
        physics_parameters=parameters,
        minimum_rows_per_state=20,
    )


@dataclass
class DemoFleet:
    pipeline: FleetPipeline
    temporary_directory: tempfile.TemporaryDirectory[str] | None

    def tick(self) -> dict[str, PipelineResult]:
        return self.pipeline.tick()

    def inject_ws_spindle(self) -> None:
        source = self.pipeline.machines["wafer_saw"].source
        assert isinstance(source, SyntheticTelemetrySource)
        source.inject_fault("spindle", strength=1.35)

    def clear_ws_fault(self) -> None:
        source = self.pipeline.machines["wafer_saw"].source
        assert isinstance(source, SyntheticTelemetrySource)
        source.clear_fault()

    def close(self) -> None:
        if self.temporary_directory is not None:
            self.temporary_directory.cleanup()
            self.temporary_directory = None


def create_demo_fleet(
    *,
    database_path: str | Path | None = None,
    knowledge_path: str | Path | None = None,
    prewarm: bool = True,
) -> DemoFleet:
    temporary: tempfile.TemporaryDirectory[str] | None = None
    if database_path is None:
        temporary = tempfile.TemporaryDirectory(prefix="osat-fleet-command-")
        database_path = Path(temporary.name) / "demo-tickets.sqlite"
    if knowledge_path is None:
        knowledge_path = DEFAULT_MANUALS_PATH
    repository = MaintenanceRepository(database_path)
    manuals = load_oem_manuals(knowledge_path)
    machines: dict[str, MachinePipeline] = {}
    for family, station in STATIONS.items():
        identity = _demo_identity(station)
        machines[family] = MachinePipeline(
            identity=identity,
            station=station,
            source=SyntheticTelemetrySource(identity, station),
            repository=repository,
            manual_chunks=manuals,
            machine_model=_fit_demo_model(identity, station),
        )
    demo = DemoFleet(FleetPipeline(machines, repository), temporary)
    if prewarm:
        for _ in range(70):
            demo.tick()
    return demo


def run_demo() -> dict[str, object]:
    demo = create_demo_fleet()
    try:
        demo.inject_ws_spindle()
        results: dict[str, PipelineResult] = {}
        for _ in range(75):
            results.update(demo.tick())
        tickets = list_tickets(demo.pipeline.repository)
        return {
            "version": VERSION,
            "release": RELEASE_CLASS,
            "production_qualified": False,
            "machines": len(demo.pipeline.machines),
            "states": {
                family: result.assessment.health_state.value
                for family, result in results.items()
            },
            "ws01_subsystems": list(
                results["wafer_saw"].assessment.suspected_subsystems
            ),
            "tickets": [
                {
                    "ticket_id": ticket.ticket_id,
                    "machine_id": ticket.machine_id,
                    "priority": ticket.priority,
                    "health_state": ticket.health_state,
                    "demo_only": ticket.demo_only,
                }
                for ticket in tickets
            ],
        }
    finally:
        demo.close()
