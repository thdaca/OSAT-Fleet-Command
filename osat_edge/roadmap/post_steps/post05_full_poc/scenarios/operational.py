"""Synthetic scenario inputs only; MachinePipeline owns every PHM decision."""
from dataclasses import replace
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys

from .....pipeline import MachinePipeline
from ....pre_steps.pre01_common.pre01_common import EquipmentState, RuntimeMode
from ....pre_steps.pre01_common.core.authority import require_shadow_permission
from ....steps.step07_machine_model.core.model_io import (
    MachineModelArtifactError, canonical_bytes, load_machine_model,
)
from ....steps.step08_live_telemetry.step08_live_telemetry import NoNewTelemetry, TelemetryBatch, QueuedTelemetrySource
from ....steps.step11a_maintenance_db.step11a_maintenance_db import MaintenanceRepository
from ....steps.step11b_oem_manuals.step11b_oem_manuals import load_oem_manuals
from ...post01_demo.post01_demo import SyntheticTelemetrySource, DEMO_START
from .onboarding import IDENTITY, STATION
from ..core.trace import decision_trace, store_identity

RESOURCES = Path(__file__).resolve().parents[1] / "resources"


class PocSource:
    """Explicit scenario controls around POST01's unchanged synthetic generator."""
    runtime_mode = RuntimeMode.SIMULATION

    def __init__(self, *, started_at=DEMO_START + dt.timedelta(seconds=360)):
        self.generator = SyntheticTelemetrySource(IDENTITY, STATION, started_at=started_at)
        self.identity, self.profile, self.origin = IDENTITY, STATION, self.generator.origin
        self.context = EquipmentState.PROCESSING
        self.omit_channel = None
        self.connected = True

    def poll(self):
        require_shadow_permission("telemetry_ingestion")
        if not self.connected:
            raise NoNewTelemetry("PoC simulated connection is unavailable")
        batch = self.generator.poll()
        return TelemetryBatch(tuple(s for s in batch.samples if s.channel != self.omit_channel),
                              replace(batch.context, equipment_state=self.context))


def make_pipeline(repository, model=None, source=None):
    require_shadow_permission("health_assessment")
    return MachinePipeline(identity=IDENTITY, station=STATION, source=source or PocSource(),
                           repository=repository, machine_model=model,
                           manual_chunks=load_oem_manuals(RESOURCES / "poc_maintenance.json"))


def monitoring_run(pipeline, record):
    for index in range(80):
        record(pipeline, "healthy_monitoring", force=index == 79)
    pipeline.source.generator.inject_fault("spindle", strength=0)
    for index in range(1, 151):
        # Input design, not a threshold change: POST01's existing fault generator.
        pipeline.source.generator.injection_strength = index * 0.000003
        record(pipeline, "progressive_spindle", force=index == 150)


def run_operational(workspace, loaded, load_options):
    repository = MaintenanceRepository(workspace / "tickets.sqlite")
    traces = []

    def record(pipeline, checkpoint, *, force=False, wall_now=None):
        previous = pipeline.last_result.assessment.health_state.value if pipeline.last_result else "UNKNOWN"
        prior = repository.active_for_machine(IDENTITY.machine_id)
        result = pipeline.tick(wall_now=wall_now)
        if force or result.assessment.transitioned:
            traces.append(decision_trace(checkpoint, pipeline, result, previous,
                                         loaded.artifact_sha256 if pipeline.machine_model else None, prior))
        return result

    cold = make_pipeline(repository, source=PocSource(started_at=DEMO_START))
    for _ in range(80):
        result = record(cold, "cold_start")
    record(cold, "cold_start", force=True)
    outcomes = {"cold_start": result.assessment.health_state.value}
    pipeline = make_pipeline(repository, loaded.model)
    monitoring_run(pipeline, record)
    critical_result = pipeline.last_result
    outcomes["healthy_operation"] = [t["health"] for t in traces if t["checkpoint"] == "healthy_monitoring"][-1]
    outcomes["progressive_spindle_anomaly"] = critical_result.assessment.health_state.value
    before_restart = repository.active_for_machine(IDENTITY.machine_id)
    restart_request = {key: value for key, value in load_options.items()
                       if key not in {"active_machine", "runtime_mode"}}
    (workspace / "reload-expectations.json").write_bytes(canonical_bytes(restart_request))
    # A fresh OS process, not just a new Python object. It replays the same inputs.
    restart = subprocess.run(
        [sys.executable, "-W", "error", "-m",
         "osat_edge.roadmap.post_steps.post05_full_poc.scenarios.restart_probe", str(workspace)],
        capture_output=True, text=True, check=True, timeout=60,
    )
    restart_report = json.loads(restart.stdout)
    expected_deviations = [t for t in traces if t["checkpoint"] == "progressive_spindle"][-1]["step07_deviations"]
    restart_report["step07_outputs_identical"] = restart_report.pop("step07_deviations") == expected_deviations
    restart_report["ticket_loaded_exactly"] = restart_report.pop("ticket_before") == before_restart
    outcomes["process_restart_model_ticket_reload"] = "PASS" if (
        restart_report["step07_outputs_identical"] and restart_report["ticket_loaded_exactly"]
        and restart_report["ticket_count"] == 1 and restart_report["ticket_id"] == before_restart["ticket_id"]
    ) else "FAIL"

    pipeline.source.generator.clear_fault()
    for index in range(90):
        result = record(pipeline, "recovery", force=index == 89)
    outcomes["recovery_under_hysteresis"] = result.assessment.health_state.value
    ticket = repository.active_for_machine(IDENTITY.machine_id)
    outcomes["ticket_remains_open_after_recovery"] = ticket["status"]

    pipeline.source.context = EquipmentState.IDLE
    result = record(pipeline, "legitimate_context_shift", force=True)
    outcomes["legitimate_context_shift"] = result.assessment.health_state.value
    pipeline.source.context = EquipmentState.PROCESSING
    for _ in range(5):
        record(pipeline, "context_restored")
    pipeline.source.omit_channel = "spindle_current"
    for index in range(35):
        result = record(pipeline, "missing_required_signal", force=index == 34)
    outcomes["missing_required_signal"] = result.assessment.health_state.value
    pipeline.source.omit_channel = None
    for _ in range(80):
        record(pipeline, "signal_restored")
    last_known = pipeline.last_result.assessment.health_state.value
    pipeline.source.connected = False
    result = record(pipeline, "stale_telemetry", force=True,
                    wall_now=pipeline.last_result.assessment.timestamp + dt.timedelta(seconds=120))
    outcomes["stale_telemetry"] = result.assessment.health_state.value
    outcomes["connectivity_loss"] = {"last_known_health": last_known, "current_health": result.assessment.health_state.value,
                                      "connection": "DISCONNECTED"}

    # Exercise the actual LIVE atomic rejection handler with synthetic simulator
    # provenance and NO live-calibrated model. Never relabel it REAL_OSAT.
    live = QueuedTelemetrySource(IDENTITY, STATION)
    live.origin = pipeline.source.origin
    malformed = make_pipeline(repository, source=live)
    source = SyntheticTelemetrySource(IDENTITY, STATION)
    for _ in range(80):
        batch = source.poll()
        live.submit(batch.samples, context=batch.context)
        malformed.tick(wall_now=batch.context.timestamp)
    before = store_identity(malformed)
    batch = source.poll()
    bad = replace(batch.samples[-1], source_id="UNAPPROVED-SOURCE")
    live.submit((*batch.samples[:-1], bad), context=batch.context)
    result = record(malformed, "malformed_atomic_batch", force=True, wall_now=batch.context.timestamp)
    unchanged = before == store_identity(malformed)
    next_batch = source.poll()
    live.submit(next_batch.samples, context=next_batch.context)
    alive = malformed.tick(wall_now=next_batch.context.timestamp) is not None
    outcomes["malformed_atomic_batch"] = {"health": result.assessment.health_state.value,
        "telemetry": "VALID" if result.telemetry_status.valid else "INVALID",
        "store_unchanged": unchanged, "runtime_alive": alive}
    corrupt = workspace / "corrupted-machine-model.json"
    raw = bytearray((workspace / "ws01-machine-model.json").read_bytes())
    raw[len(raw) // 2] ^= 1
    corrupt.write_bytes(raw)
    try:
        load_machine_model(corrupt, **load_options)
    except MachineModelArtifactError:
        rejected = True
    else:
        rejected = False
    no_model = make_pipeline(repository)
    for _ in range(80):
        no_model.tick()
    result = record(no_model, "corrupted_machine_model", force=True)
    outcomes["corrupted_machine_model"] = {"rejected": rejected, "health": result.assessment.health_state.value}
    return {"outcomes": outcomes, "trace": traces, "restart": restart_report,
            "tickets": repository.list_tickets(), "ticket_count": len(repository.list_tickets())}, critical_result
