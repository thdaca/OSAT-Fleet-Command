"""Step 09: subsystem-first health with direct max scoring and hysteresis."""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass

from ...pre_steps.pre01_common.pre01_common import (
    EquipmentState,
    HealthState,
    MachineIdentity,
    RuntimeMode,
    health_rank,
    utc,
)
from ...pre_steps.pre02_machine_registry.pre02_machine_registry import StationDefinition
from ..step07_machine_model.step07_machine_model import FeatureDeviation, MachineModelResult
from ..step08_live_telemetry.step08_live_telemetry import TelemetryStatus


WATCH_ENTRY = 0.35
DEGRADED_ENTRY = 0.60
CRITICAL_ENTRY = 0.82
WATCH_EXIT = 0.25
DEGRADED_EXIT = 0.48
CRITICAL_EXIT = 0.70
ENTRY_PERSISTENCE = dt.timedelta(seconds=2)
RECOVERY_PERSISTENCE = dt.timedelta(seconds=5)


@dataclass
class StateTracker:
    state: HealthState = HealthState.UNKNOWN
    entered_at: dt.datetime | None = None
    candidate: HealthState | None = None
    candidate_since: dt.datetime | None = None

    def _target(self, score: float) -> HealthState:
        if self.state is HealthState.CRITICAL:
            return HealthState.DEGRADED if score < CRITICAL_EXIT else HealthState.CRITICAL
        if self.state is HealthState.DEGRADED:
            if score >= CRITICAL_ENTRY:
                return HealthState.CRITICAL
            return HealthState.WATCH if score < DEGRADED_EXIT else HealthState.DEGRADED
        if self.state is HealthState.WATCH:
            if score >= CRITICAL_ENTRY:
                return HealthState.CRITICAL
            if score >= DEGRADED_ENTRY:
                return HealthState.DEGRADED
            return HealthState.NORMAL if score < WATCH_EXIT else HealthState.WATCH
        if score >= CRITICAL_ENTRY:
            return HealthState.CRITICAL
        if score >= DEGRADED_ENTRY:
            return HealthState.DEGRADED
        if score >= WATCH_ENTRY:
            return HealthState.WATCH
        return HealthState.NORMAL

    def reset_candidate(self) -> None:
        self.candidate = None
        self.candidate_since = None

    def update(self, score: float | None, timestamp: dt.datetime) -> tuple[HealthState, bool]:
        now = utc(timestamp)
        timeline = tuple(
            value for value in (self.entered_at, self.candidate_since) if value is not None
        )
        if any(now < value for value in timeline):
            raise ValueError("Health-state timestamps must not move backward")
        previous = self.state
        if score is None or not math.isfinite(score):
            self.state = HealthState.UNKNOWN
            self.entered_at = now
            self.reset_candidate()
            return self.state, previous is not self.state
        target = self._target(float(score))
        if target is self.state:
            self.reset_candidate()
        else:
            if target is not self.candidate:
                self.candidate = target
                self.candidate_since = now
            assert self.candidate_since is not None
            improving = health_rank(target) < health_rank(self.state)
            required = RECOVERY_PERSISTENCE if improving else ENTRY_PERSISTENCE
            if now - self.candidate_since >= required:
                self.state = target
                self.entered_at = now
                self.reset_candidate()
        if self.entered_at is None:
            self.entered_at = now
        return self.state, previous is not self.state


@dataclass(frozen=True)
class SubsystemHealth:
    subsystem: str
    state: HealthState
    score: float | None
    deviations: tuple[FeatureDeviation, ...]
    reason: str | None = None


@dataclass(frozen=True)
class HealthAssessment:
    machine: MachineIdentity
    timestamp: dt.datetime
    runtime_mode: RuntimeMode
    equipment_state: EquipmentState
    health_state: HealthState
    telemetry_valid: bool
    observable: bool
    subsystem_health: tuple[SubsystemHealth, ...]
    family_risk_score: float | None
    reason: str | None
    transitioned: bool

    @property
    def suspected_subsystems(self) -> tuple[str, ...]:
        if self.health_state not in {
            HealthState.WATCH,
            HealthState.DEGRADED,
            HealthState.CRITICAL,
        }:
            return ()
        return tuple(
            subsystem.subsystem
            for subsystem in self.subsystem_health
            if health_rank(subsystem.state) >= health_rank(self.health_state)
        )


class HealthEngine:
    def __init__(self, machine: MachineIdentity, station: StationDefinition) -> None:
        if machine.family != station.family or machine.station_id != station.station_id:
            raise ValueError("Health engine machine and station identity must match")
        self.machine = machine
        self.station = station
        self.machine_tracker = StateTracker()
        self.subsystem_trackers: dict[str, StateTracker] = {}
        self.required_subsystems = {
            channel.subsystem for channel in station.channels if channel.required
        }

    def _unknown(
        self,
        status: TelemetryStatus,
        timestamp: dt.datetime,
        runtime_mode: RuntimeMode,
        equipment_state: EquipmentState,
        reason: str,
    ) -> HealthAssessment:
        state, transitioned = self.machine_tracker.update(None, timestamp)
        for tracker in self.subsystem_trackers.values():
            tracker.update(None, timestamp)
        subsystems = tuple(
            SubsystemHealth(subsystem, HealthState.UNKNOWN, None, (), reason)
            for subsystem in self.station.subsystems
        )
        return HealthAssessment(
            machine=self.machine,
            timestamp=utc(timestamp),
            runtime_mode=runtime_mode,
            equipment_state=equipment_state,
            health_state=state,
            telemetry_valid=status.valid,
            observable=status.observable,
            subsystem_health=subsystems,
            family_risk_score=None,
            reason=reason,
            transitioned=transitioned,
        )

    def assess(
        self,
        status: TelemetryStatus,
        machine_result: MachineModelResult | None,
        *,
        timestamp: dt.datetime,
        runtime_mode: RuntimeMode,
        equipment_state: EquipmentState,
        family_risk_score: float | None = None,
    ) -> HealthAssessment:
        if not status.valid:
            return self._unknown(
                status, timestamp, runtime_mode, equipment_state,
                status.issues[0] if status.issues else "Required telemetry is invalid",
            )
        if not status.observable:
            return self._unknown(
                status, timestamp, runtime_mode, equipment_state,
                status.issues[0] if status.issues else "Telemetry is not observable",
            )
        if machine_result is None or not machine_result.available:
            return self._unknown(
                status, timestamp, runtime_mode, equipment_state,
                machine_result.reason if machine_result else "Exact-machine model is unavailable",
            )

        by_subsystem: dict[str, list[FeatureDeviation]] = {}
        for deviation in machine_result.deviations:
            by_subsystem.setdefault(deviation.subsystem, []).append(deviation)
        results: list[SubsystemHealth] = []
        scores: list[float] = []
        for subsystem in self.station.subsystems:
            deviations = tuple(by_subsystem.get(subsystem, ()))
            eligible = [
                deviation.score
                for deviation in deviations
                if deviation.kind in {"location", "physics"}
            ]
            if not eligible:
                if subsystem in self.required_subsystems:
                    return self._unknown(
                        status, timestamp, runtime_mode, equipment_state,
                        f"Required subsystem {subsystem} has no scoreable evidence",
                    )
                results.append(
                    SubsystemHealth(
                        subsystem, HealthState.UNKNOWN, None, deviations,
                        "No scoreable current evidence",
                    )
                )
                continue
            score = max(eligible)
            tracker = self.subsystem_trackers.setdefault(subsystem, StateTracker())
            state, _ = tracker.update(score, timestamp)
            results.append(SubsystemHealth(subsystem, state, score, deviations))
            scores.append(score)
        if not scores:
            return self._unknown(
                status, timestamp, runtime_mode, equipment_state,
                "No scoreable subsystem evidence",
            )
        machine_score = max(scores)
        machine_state, transitioned = self.machine_tracker.update(machine_score, timestamp)
        reason = None
        if family_risk_score is not None:
            reason = (
                "Uncalibrated family risk is advisory research evidence and does not "
                "alter the health state."
            )
        if runtime_mode is RuntimeMode.LIVE_EQUIPMENT:
            observe_only = "LIVE_EQUIPMENT is OBSERVE ONLY; no actionable ticket is authorized."
            reason = f"{reason} {observe_only}".strip() if reason else observe_only
        elif runtime_mode is RuntimeMode.REAL_REPLAY:
            replay_only = "RESEARCH REPLAY; no actionable maintenance authority."
            reason = f"{reason} {replay_only}".strip() if reason else replay_only
        return HealthAssessment(
            machine=self.machine,
            timestamp=utc(timestamp),
            runtime_mode=runtime_mode,
            equipment_state=equipment_state,
            health_state=machine_state,
            telemetry_valid=status.valid,
            observable=status.observable,
            subsystem_health=tuple(results),
            family_risk_score=family_risk_score,
            reason=reason,
            transitioned=transitioned,
        )
