"""POST02 run a validated synthetic artifact through the operational pipeline."""
from __future__ import annotations
import tempfile
from pathlib import Path
from typing import Any
from ...pre_steps.pre01_common.contracts import DataOrigin, RuntimeMode, VERSION
from ....pipeline import MachinePipeline, PipelineResult
from ..post01_demo.demo import fit_demo_model
from ...steps.step11a_maintenance_db.repository import MaintenanceRepository
from ...steps.step11b_oem_manuals.manuals import DEFAULT_MANUALS_PATH, load_oem_manuals
from ...steps.step15_maintenance_ticket.tickets import list_tickets
from .artifact import (
    DEFAULT_REFERENCE_DIRECTORY,
    ReferenceReplayError,
    load_reference_replay,
    _utc_timestamp,
)


def _checkpoint_observation(
    result: PipelineResult,
    *,
    ticket_created_this_tick: bool,
    active_ticket_count: int,
) -> dict[str, Any]:
    relation_name = "spindle.electromechanical_load_residual_a.median"
    residual = None
    if result.feature_set is not None:
        feature = result.feature_set.by_name.get(relation_name)
        if feature is not None:
            residual = feature.value
    return {
        "health": result.assessment.health_state.value,
        "telemetry_valid": result.telemetry_status.valid,
        "observable": result.telemetry_status.observable,
        "physics_residual_present": residual is not None,
        "physics_residual_a": residual,
        "ticket_created_this_tick": ticket_created_this_tick,
        "active_ticket_count": active_ticket_count,
    }


def run_reference_replay(
    directory: str | Path = DEFAULT_REFERENCE_DIRECTORY,
    *,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Run the frozen artifact. Expected checkpoints never influence inference."""

    dataset = load_reference_replay(directory)
    temporary: tempfile.TemporaryDirectory[str] | None = None
    if database_path is None:
        temporary = tempfile.TemporaryDirectory(prefix="osat-reference-replay-")
        database_path = Path(temporary.name) / "reference-tickets.sqlite"
    repository = MaintenanceRepository(database_path)
    manuals = load_oem_manuals(DEFAULT_MANUALS_PATH)
    model = fit_demo_model(dataset.identity, dataset.station)
    pipeline = MachinePipeline(
        identity=dataset.identity,
        station=dataset.station,
        source=dataset.source,
        repository=repository,
        manual_chunks=manuals,
        machine_model=model,
    )
    expected_by_time = {
        _utc_timestamp(str(row["timestamp_utc"]), "checkpoint timestamp"): str(row["name"])
        for row in dataset.expected_checkpoints["checkpoints"]
    }
    checkpoints: dict[str, dict[str, Any]] = {}
    health_counts: dict[str, int] = {}
    valid_ticks = 0
    invalid_ticks = 0
    residual_ticks = 0
    abstention_ticks = 0
    positive_residual_ticks = 0
    maximum_residual: float | None = None
    last: PipelineResult | None = None
    tick_count = 0
    known_ticket_ids: set[str] = set()
    try:
        while True:
            result = pipeline.tick()
            if result is None:
                break
            last = result
            tick_count += 1
            state = result.assessment.health_state.value
            health_counts[state] = health_counts.get(state, 0) + 1
            if result.telemetry_status.valid:
                valid_ticks += 1
            else:
                invalid_ticks += 1
            relation = None
            if result.feature_set is not None:
                relation = result.feature_set.by_name.get(
                    "spindle.electromechanical_load_residual_a.median"
                )
                if relation is None:
                    abstention_ticks += 1
                else:
                    residual_ticks += 1
                    if relation.value > 0.0:
                        positive_residual_ticks += 1
                        maximum_residual = (
                            relation.value
                            if maximum_residual is None
                            else max(maximum_residual, relation.value)
                        )
            checkpoint_name = expected_by_time.get(result.assessment.timestamp)
            ticket_created_this_tick = bool(
                result.ticket is not None
                and result.ticket.ticket_id not in known_ticket_ids
            )
            if result.ticket is not None:
                known_ticket_ids.add(result.ticket.ticket_id)
            if checkpoint_name is not None:
                checkpoints[checkpoint_name] = _checkpoint_observation(
                    result,
                    ticket_created_this_tick=ticket_created_this_tick,
                    active_ticket_count=int(
                        repository.active_for_machine(dataset.identity.machine_id)
                        is not None
                    ),
                )
        if last is None:
            raise ReferenceReplayError("Reference replay produced no pipeline result")
        tickets = list_tickets(repository)
        expected_final = str(dataset.expected_checkpoints["expected_final_state"])
        if last.assessment.health_state.value != expected_final:
            raise ReferenceReplayError(
                "Observed final health does not match expected_final_state"
            )
        if not tickets:
            raise ReferenceReplayError("Expected replay ticket was not produced")
        expected_priority = str(dataset.expected_checkpoints["expected_ticket_priority"])
        if tickets[0].priority != expected_priority:
            raise ReferenceReplayError(
                "Observed ticket priority does not match expected_ticket_priority"
            )
        expected_subsystem = str(dataset.expected_checkpoints["expected_subsystem"])
        if expected_subsystem not in tickets[0].suspected_subsystems:
            raise ReferenceReplayError(
                "Observed ticket subsystem does not match expected_subsystem"
            )
        return {
            "version": VERSION,
            "dataset_id": dataset.manifest["dataset_id"],
            "schema_version": dataset.manifest["schema_version"],
            "origin": DataOrigin.SYNTHETIC.value,
            "runtime_mode": RuntimeMode.REAL_REPLAY.value,
            "machine_id": dataset.identity.machine_id,
            "family": dataset.identity.family,
            "station_id": dataset.identity.station_id,
            "telemetry_rows": dataset.telemetry_rows,
            "input_telemetry_rows": dataset.telemetry_rows,
            "accepted_telemetry_rows": dataset.telemetry_rows,
            "rejected_telemetry_rows": 0,
            "context_rows": dataset.context_rows,
            "accepted_context_rows": dataset.context_rows,
            "rejected_context_rows": 0,
            "ticks": tick_count,
            "valid_ticks": valid_ticks,
            "invalid_ticks": invalid_ticks,
            "health_counts": health_counts,
            "physics_residual_ticks": residual_ticks,
            "physics_abstention_ticks": abstention_ticks,
            "positive_residual_ticks": positive_residual_ticks,
            "maximum_positive_residual_a": maximum_residual,
            "checkpoint_observations": checkpoints,
            "tickets": [ticket.to_payload() for ticket in tickets],
            "final_health": last.assessment.health_state.value,
            "model_source": "deterministic synthetic healthy calibration using the existing demo calibration path",
            "claims": [
                "SYNTHETIC REFERENCE REPLAY",
                "DEVELOPMENT-ONLY RESEARCH PIPELINE DEMONSTRATION",
                "NOT REAL OSAT DATA",
                "NOT PLANT VALIDATION",
                "NOT PRODUCTION QUALIFICATION",
            ],
        }
    finally:
        if temporary is not None:
            temporary.cleanup()
