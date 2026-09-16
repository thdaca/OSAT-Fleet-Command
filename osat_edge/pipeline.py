"""Linear orchestrator that reads like the OSAT Fleet Command roadmap."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Mapping, Sequence

from .common import DataOrigin, EquipmentState, HealthState, MachineIdentity, RuntimeMode
from .machines import StationDefinition
from .roadmap.step02_physical_features import FeatureSet, extract_physical_features
from .roadmap.step03_physical_residuals import calculate_physical_residuals
from .roadmap.step05_family_model import FamilyModel, score_family_model
from .roadmap.step07_machine_model import (
    MachineModel,
    MachineModelResult,
    evaluate_machine_model,
    validate_machine_model,
)
from .roadmap.step08_live_telemetry import (
    FEATURE_WINDOW,
    BoundedTelemetryStore,
    NoNewTelemetry,
    TelemetrySource,
    TelemetrySourceExhausted,
    assess_telemetry,
)
from .roadmap.step09_health_risk import HealthAssessment, HealthEngine
from .roadmap.step10_fault_evidence import FaultEvidence, build_fault_evidence
from .roadmap.step11a_maintenance_db import MaintenanceRepository
from .roadmap.step11b_oem_manuals import ManualChunk
from .roadmap.step12_rag import retrieve_rag_context
from .roadmap.step13_local_llm import generate_local_llm_json
from .roadmap.step14_json_validation import validate_llm_json
from .roadmap.step15_maintenance_ticket import MaintenanceTicket, create_or_update_ticket


@dataclass(frozen=True)
class PipelineResult:
    assessment: HealthAssessment
    fault_evidence: FaultEvidence | None
    ticket: MaintenanceTicket | None


class MachinePipeline:
    def __init__(
        self,
        *,
        identity: MachineIdentity,
        station: StationDefinition,
        source: TelemetrySource,
        repository: MaintenanceRepository,
        manual_chunks: Sequence[ManualChunk] = (),
        machine_model: MachineModel | None = None,
        family_model: FamilyModel | None = None,
        llm_model_path: str | Path | None = None,
    ) -> None:
        if identity.family != station.family or identity.station_id != station.station_id:
            raise ValueError("Active machine and station identity must match")
        if source.identity != identity or source.profile != station:
            raise ValueError("Telemetry source identity/profile does not match active machine")
        if machine_model is not None:
            validate_machine_model(machine_model, identity, source.runtime_mode)
        if family_model is not None:
            if family_model.family != identity.family:
                raise ValueError(
                    f"Family model for {family_model.family} cannot attach to {identity.family}"
                )
            if (
                source.runtime_mode is not RuntimeMode.SIMULATION
                and family_model.origin is not DataOrigin.REAL_OSAT
            ):
                raise ValueError("REAL_REPLAY/LIVE_EQUIPMENT reject synthetic family models")
        self.identity = identity
        self.station = station
        self.source = source
        self.repository = repository
        self.manual_chunks = tuple(manual_chunks)
        self.machine_model = machine_model
        self.family_model = family_model
        self.llm_model_path = llm_model_path
        self.store = BoundedTelemetryStore(identity, station)
        self.health = HealthEngine(identity, station)
        self.monitored = True
        self.last_result: PipelineResult | None = None

    def _poll(self) -> dt.datetime:
        batch = self.source.poll()
        self.store.append_batch(batch)
        timestamps = [sample.timestamp for sample in batch.samples]
        if batch.context is not None:
            timestamps.append(batch.context.timestamp)
        if not timestamps:
            raise NoNewTelemetry("Telemetry source returned an empty batch")
        return max(timestamps)

    def tick(self, *, wall_now: dt.datetime | None = None) -> PipelineResult | None:
        if not self.monitored:
            return None
        try:
            now = self._poll()
        except NoNewTelemetry:
            now = wall_now or dt.datetime.now(dt.timezone.utc)
        except TelemetrySourceExhausted:
            return self.last_result

        windows = self.store.windows(
            [channel.name for channel in self.station.channels],
            end=now,
            duration=FEATURE_WINDOW,
        )
        status = assess_telemetry(self.store, now=now, windows=windows)
        context = self.store.latest_context(now)
        equipment_state = (
            context.equipment_state if context is not None else EquipmentState.UNKNOWN
        )

        feature_set: FeatureSet | None = None
        machine_result: MachineModelResult | None = None
        family_risk: float | None = None
        if status.valid and status.observable and self.machine_model is not None:
            usable = {
                name: window
                for name, window in windows.items()
                if name in status.usable_channels
            }
            feature_set = extract_physical_features(
                self.identity,
                self.station,
                usable,
                timestamp=now,
                equipment_state=equipment_state,
                window_start=now - FEATURE_WINDOW,
            )
            residuals = calculate_physical_residuals(
                self.identity.family,
                usable,
                fitted_parameters=self.machine_model.physics_parameters,
            )
            feature_set = replace(
                feature_set, features=feature_set.features + residuals
            )
            machine_result = evaluate_machine_model(
                self.machine_model,
                self.identity,
                feature_set,
                runtime_mode=self.source.runtime_mode,
            )
            if self.family_model is not None:
                family_features = {
                    name: feature.value for name, feature in feature_set.by_name.items()
                }
                if all(name in family_features for name in self.family_model.feature_names):
                    family_risk = score_family_model(
                        self.family_model,
                        active_family=self.identity.family,
                        features=family_features,
                        runtime_mode=self.source.runtime_mode,
                    )

        assessment = self.health.assess(
            status,
            machine_result,
            timestamp=now,
            runtime_mode=self.source.runtime_mode,
            equipment_state=equipment_state,
            family_risk_score=family_risk,
        )
        fault_evidence = build_fault_evidence(assessment)
        ticket = None
        if (
            assessment.transitioned
            and assessment.health_state in {HealthState.DEGRADED, HealthState.CRITICAL}
            and fault_evidence is not None
            and self.source.runtime_mode is RuntimeMode.SIMULATION
        ):
            try:
                prior = self.repository.prior_context(self.identity.machine_id)
                passages = retrieve_rag_context(
                    fault_evidence, prior, self.manual_chunks
                )
            except Exception:
                passages = ()
            raw = generate_local_llm_json(
                fault_evidence, passages, model_path=self.llm_model_path
            )
            enrichment = validate_llm_json(raw, fault_evidence, passages)
            ticket = create_or_update_ticket(
                self.repository, fault_evidence, enrichment
            )
        result = PipelineResult(assessment, fault_evidence, ticket)
        self.last_result = result
        return result


class FleetPipeline:
    def __init__(
        self,
        machines: Mapping[str, MachinePipeline],
        repository: MaintenanceRepository,
    ) -> None:
        self.machines = dict(machines)
        self.repository = repository
        self.connected = True

    @property
    def link_state(self) -> str:
        return "CONNECTED" if self.connected else "DISCONNECTED"

    def tick(self, *, wall_now: dt.datetime | None = None) -> dict[str, PipelineResult]:
        if not self.connected:
            return {}
        results: dict[str, PipelineResult] = {}
        for family, machine in self.machines.items():
            result = machine.tick(wall_now=wall_now)
            if result is not None:
                results[family] = result
        return results

    def set_connected(self, connected: bool) -> None:
        self.connected = bool(connected)

    def set_monitored(self, family: str, monitored: bool) -> None:
        self.machines[family].monitored = bool(monitored)
