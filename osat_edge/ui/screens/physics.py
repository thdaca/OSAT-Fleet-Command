"""PHYSICS screen: presentation only; health and authority are decided by the pipeline."""

from __future__ import annotations

import math

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPlainTextEdit,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ...roadmap.steps.step01_physics_library.library import (
    RESIDUAL_SCALE,
    SPEED_HIGH,
    SPEED_LOW,
    SPEED_SPAN,
    PhysicsRelation,
    ResearchCandidate,
    audit_physics_library,
    physics_readiness_report,
    research_catalog_for_family,
)


from ..widgets import format_value, joined, make_table, set_row

class PhysicsScreen(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self._physics_items: list[PhysicsRelation | ResearchCandidate] = []
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self.physics_status = QLabel("PHYSICS EVIDENCE: NOT AVAILABLE")
        self.physics_status.setObjectName("section")
        self.physics_audit = QLabel("PHYSICS LIBRARY AUDIT: NOT AVAILABLE")
        self.physics_audit.setObjectName("instrument")
        top.addWidget(self.physics_status)
        top.addStretch(1)
        top.addWidget(self.physics_audit)
        layout.addLayout(top)
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.physics_table = make_table(
            ("STATUS", "MATURITY", "RELATION", "SUBSYSTEM", "OUTPUT", "CURRENT", "UNIT", "DOMAIN", "PRIMARY BLOCKER"),
            "Step01 physics research catalog table",
        )
        physics_header = self.physics_table.horizontalHeader()
        for column, width in enumerate((100, 135, 205, 80, 215, 165, 50, 140)):
            physics_header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)
            self.physics_table.setColumnWidth(column, width)
        physics_header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)
        self.physics_table.itemSelectionChanged.connect(self._show_physics_detail)
        splitter.addWidget(self.physics_table)
        self.physics_detail = QPlainTextEdit()
        self.physics_detail.setReadOnly(True)
        self.physics_detail.setAccessibleName("Selected physics relation research detail")
        splitter.addWidget(self.physics_detail)
        splitter.setSizes([260, 340])
        layout.addWidget(splitter, 1)

    def _physics_deviations(self) -> dict[str, object]:
        result = self.window.selected_machine.last_result
        if result is None:
            return {}
        return {
            deviation.feature: deviation
            for subsystem in result.assessment.subsystem_health
            for deviation in subsystem.deviations
            if deviation.kind == "physics"
        }

    def _physics_runtime_view(self, item: PhysicsRelation) -> tuple[str, str, str]:
        machine = self.window.selected_machine
        result = machine.last_result
        features = () if result is None else tuple(
            feature
            for feature in result.feature_set.features
            if feature.relation_id == item.relation_id
        )
        feature = features[0] if features else None
        deviation = None if feature is None else self._physics_deviations().get(feature.name)
        current_value = format_value(feature.value) if feature is not None else "NOT AVAILABLE"
        if deviation is None:
            contribution = "HEALTH CONTRIBUTION: NOT SCORED / NOT AVAILABLE"
        else:
            contribution = (
                f"HEALTH CONTRIBUTION: {deviation.score:.3f} · "
                f"{deviation.z_score:+.2f} ROBUST SCALES"
            )

        parameters = (
            machine.machine_model.physics_parameters.get(item.relation_id, {})
            if machine.machine_model is not None
            else {}
        )
        low = parameters.get(SPEED_LOW)
        high = parameters.get(SPEED_HIGH)
        span = parameters.get(SPEED_SPAN)
        scale = parameters.get(RESIDUAL_SCALE)
        calibrated = all(
            value is not None and math.isfinite(value)
            for value in (low, high, span, scale)
        )
        if calibrated:
            latest_speed = machine.store.latest("spindle_speed")
            if latest_speed is None:
                domain = "LATEST INPUT: NOT AVAILABLE"
            elif low <= latest_speed.value <= high:
                domain = "LATEST INPUT: IN CALIBRATED RANGE"
            else:
                domain = "LATEST INPUT: OUTSIDE CALIBRATED RANGE"
            calibration = (
                f"CALIBRATED SPEED RANGE\n{low:,.0f} – {high:,.0f} RPM\n\n"
                f"CALIBRATED SPEED SPAN\n{span:,.0f} RPM\n\n"
                f"HEALTHY RESIDUAL SCALE\n{scale:.7g} A\n\n{domain}"
            )
        else:
            domain = "CALIBRATION RANGE: NOT AVAILABLE"
            calibration = domain
        output_label = (
            "CURRENT PHYSICS OUTPUT"
            if self.window.pipeline.connected
            else "LAST KNOWN PHYSICS OUTPUT"
        )
        runtime_detail = (
            f"{output_label}\n{item.output_name}: {current_value} {item.output_unit}\n"
            f"{contribution}\n\n{calibration}"
        )
        return current_value, domain, runtime_detail

    def refresh(self) -> None:
        machine = self.window.selected_machine
        previous_id = None
        row = self.physics_table.currentRow()
        if 0 <= row < len(self._physics_items):
            previous_id = self._item_id(self._physics_items[row])
        self._physics_items = list(research_catalog_for_family(machine.identity.family))
        readiness = {entry.item_id: entry for entry in physics_readiness_report()}
        self.physics_table.setRowCount(len(self._physics_items))
        for row, item in enumerate(self._physics_items):
            item_id = self._item_id(item)
            entry = readiness.get(item_id)
            if isinstance(item, PhysicsRelation):
                current, domain, _ = self._physics_runtime_view(item)
                output, unit = item.output_name, item.output_unit
            else:
                current, domain, output, unit = "N/A — NOT RUNTIME", "NOT RUNTIME", "N/A", "N/A"
            values = (
                item.status.value,
                item.evidence_maturity.value,
                item_id,
                item.subsystem,
                output,
                current if self.window.pipeline.connected else f"LAST KNOWN · {current}",
                unit,
                domain,
                entry.major_blocker if entry else item.major_blocker,
            )
            set_row(self.physics_table, row, values)
        issues = audit_physics_library()
        self.physics_audit.setText("PHYSICS LIBRARY AUDIT: PASS — INTERNAL CONSISTENCY ONLY" if not issues else f"PHYSICS LIBRARY AUDIT: {len(issues)} ISSUES")
        current = "LAST KNOWN PHYSICS EVIDENCE" if not self.window.pipeline.connected else "CURRENT PHYSICS EVIDENCE"
        self.physics_status.setText(
            f"{machine.identity.station_id} · {current} · {len(self._physics_items)} CATALOG ITEMS · RELATION OUTPUT IS NOT A DIAGNOSIS"
        )
        selected = next((index for index, item in enumerate(self._physics_items) if self._item_id(item) == previous_id), 0)
        if self._physics_items:
            self.physics_table.selectRow(selected)
            self._show_physics_detail()
        else:
            self.physics_detail.setPlainText("NO PHYSICS CATALOG ITEMS — NOT AVAILABLE")

    @staticmethod
    def _item_id(item: PhysicsRelation | ResearchCandidate) -> str:
        return item.relation_id if isinstance(item, PhysicsRelation) else item.candidate_id

    def _show_physics_detail(self) -> None:
        row = self.physics_table.currentRow()
        if not 0 <= row < len(self._physics_items):
            self.physics_detail.setPlainText("NOT AVAILABLE")
            return
        item = self._physics_items[row]
        item_id = self._item_id(item)
        claims = "\n".join(
            f"- {claim.statement} [scope: {claim.evidence_scope}; limits: {claim.limitations}]"
            for claim in item.evidence_claims
        ) or "NOT AVAILABLE"
        measurements = "\n".join(
            f"- {requirement.channel}: {requirement.measurand} [{requirement.required_unit}] · {requirement.status.value} · {requirement.semantics_required}"
            for requirement in item.measurement_requirements
        ) or "NOT AVAILABLE"
        parameters = "\n".join(
            f"- {parameter.name} [{parameter.unit}] · {parameter.source.value} · {parameter.identifiability_notes}"
            for parameter in getattr(item, "parameter_specs", ())
        ) or "NOT AVAILABLE"
        uncertainty = getattr(item, "measurement_uncertainty_sources", getattr(item, "uncertainty_sources", ()))
        discrepancy = item.model_discrepancy_sources
        sensitivities = "\n".join(
            f"- {value.mechanism_or_fault}: {value.expected_direction.value} · {value.evidence_maturity.value} · {value.rationale}"
            for value in item.target_fault_sensitivities
        ) or "NOT AVAILABLE"
        sensor_faults = "\n".join(
            f"- {value.channel}: {value.failure_mode} · {value.effect_on_output} · can mimic degradation: {'YES' if value.can_mimic_degradation else 'NO'}"
            for value in item.sensor_failure_modes
        ) or "NOT AVAILABLE"
        references = "\n".join(
            f"- {reference.key}: {reference.citation} ({reference.publication_year or 'year not available'}) · {reference.identifier} · limits: {reference.scope_limitations}"
            for reference in item.references
        ) or "NOT AVAILABLE"
        equation = item.equation if isinstance(item, PhysicsRelation) else item.proposed_equation
        mechanism = item.mechanism if isinstance(item, PhysicsRelation) else item.proposed_mechanism
        validity = getattr(item, "validity_conditions", ())
        invalidity = getattr(item, "invalidity_conditions", ())
        calibration = getattr(item, "calibration_requirements", ())
        cross = getattr(item, "cross_sensitivities", ())
        confounders = getattr(item, "confounders", ())
        missing = getattr(item, "missing_variables", ())
        output = f"{item.output_name} [{item.output_unit}]" if isinstance(item, PhysicsRelation) else "NOT RUNTIME"
        decision = getattr(item, "decision_reason", "NOT AVAILABLE")
        runtime_detail = (
            self._physics_runtime_view(item)[2]
            if isinstance(item, PhysicsRelation)
            else "NOT RUNTIME"
        )
        sections = (
            ('RELATION ID', f"{item_id}"),
            ('STATUS / EVIDENCE MATURITY / KIND', f"{item.status.value} · {item.evidence_maturity.value} · {item.kind.value}"),
            ('DESCRIPTION / PROPOSED MECHANISM', f"{item.description}\n{mechanism}"),
            ('EXACT ENGINEERING CLAIMS', f"{claims}"),
            ('EQUATION', f"{equation}"),
            ('OUTPUT + UNIT', f"{output}"),
            ('REQUIRED MEASUREMENTS / MEASUREMENT-SEMANTIC STATUS', f"{measurements}"),
            ('MISSING VARIABLES', f"{joined(missing)}"),
            ('VALIDITY CONDITIONS', f"{joined(validity)}"),
            ('INVALIDITY CONDITIONS', f"{joined(invalidity)}"),
            ('CALIBRATION REQUIREMENTS', f"{joined(calibration)}"),
            ('PARAMETER IDENTIFIABILITY', f"{parameters}"),
            ('CALIBRATION / APPLICABILITY ENVELOPE', f"{runtime_detail}"),
            ('MEASUREMENT UNCERTAINTY SOURCES', f"{joined(f'- {value.name}: {value.category.value} · {value.description}' for value in uncertainty)}"),
            ('MODEL DISCREPANCY SOURCES', f"{joined(f'- {value.name}: {value.category.value} · {value.description}' for value in discrepancy)}"),
            ('FAULT SENSITIVITIES', f"{sensitivities}"),
            ('CROSS-SENSITIVITIES', f"{joined(cross)}"),
            ('SENSOR-FAULT SENSITIVITIES', f"{sensor_faults}"),
            ('CONFOUNDERS', f"{joined(confounders)}"),
            ('FALSIFICATION CRITERIA', f"{joined(item.falsification_tests)}"),
            ('RECALIBRATION TRIGGERS', f"{joined(item.recalibration_triggers)}"),
            ('RESEARCH DECISION REASON', f"{decision}"),
            ('MAJOR BLOCKER', f"{item.major_blocker}"),
            ('NEXT EXPERIMENT', f"{item.next_experiment}"),
            ('SUPPORTING REFERENCES', f"{references}"),
        )
        detail = "\n\n".join(f"{heading}\n{value}" for heading, value in sections) + "\n"
        self.physics_detail.setPlainText(detail)
