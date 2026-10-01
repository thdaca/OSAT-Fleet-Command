"""SYSTEM screen: presentation only; health and authority are decided by the pipeline."""

from __future__ import annotations


from PyQt6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget

from ...roadmap.pre_steps.pre01_common.contracts import RELEASE_CLASS, RuntimeMode, VERSION


class SystemScreen(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        layout = QVBoxLayout(self)
        self.system_text = QPlainTextEdit()
        self.system_text.setReadOnly(True)
        self.system_text.setAccessibleName("Runtime security and authority transparency")
        layout.addWidget(self.system_text)

    def refresh(self) -> None:
        machine = self.window.selected_machine
        result = machine.last_result
        assessment = result.assessment if result else None
        exact_origin = machine.machine_model.origin.value if machine.machine_model else "NOT AVAILABLE"
        family_origin = machine.family_model.origin.value if machine.family_model else "NOT AVAILABLE"
        usable = len(result.telemetry_status.usable_channels) if result else 0
        required = sum(channel.required for channel in machine.station.channels)
        mode = machine.source.runtime_mode
        authority = "DEMO TICKETS ONLY" if mode is RuntimeMode.SIMULATION else "OBSERVE ONLY — NO MAINTENANCE AUTHORITY"
        llm = "CONFIGURED — LOCAL ONLY" if machine.llm_model_path else "NOT CONFIGURED"
        timestamp = assessment.timestamp.isoformat() if assessment else "NOT AVAILABLE"
        self.system_text.setPlainText(f"""SOFTWARE
PRODUCT: OSAT SemiGuard
VERSION: {VERSION}
RELEASE CLASS: {RELEASE_CLASS}
QUALIFICATION: NOT PRODUCTION QUALIFIED

RUNTIME
CONNECTION STATE: {self.window.pipeline.link_state}
SOURCE TYPE: {type(machine.source).__name__}
RUNTIME MODE: {mode.value}
DECLARED DATA ORIGIN: {machine.source.origin.value}
SELECTED MACHINE: {machine.identity.station_id} / {machine.identity.machine_id}
ASSESSMENT TIMESTAMP: {timestamp}
CURRENTNESS: {'CURRENT' if self.window.pipeline.connected else 'LAST KNOWN — NOT CURRENT'}

DATA
EXACT-MACHINE MODEL ORIGIN: {exact_origin}
FAMILY-MODEL ORIGIN: {family_origin}
CANONICAL CHANNEL COUNT: {len(machine.station.channels)}
REQUIRED CHANNEL COUNT: {required}
USABLE CHANNEL COUNT: {usable}

TELEMETRY SECURITY
EXPLICIT APPROVED SOURCE-ID TO CANONICAL-CHANNEL MAPPING
UNKNOWN SOURCE IDs ARE REJECTED
UNAPPROVED PROCESS-IP FIELDS ARE REJECTED
CURRENT SOURCE IDs ARE VISIBLE IN THE MACHINE TELEMETRY TABLE

MAINTENANCE AUTHORITY
{authority}
THIS SOFTWARE DOES NOT CONTROL OR SHUT DOWN EQUIPMENT

LLM
STATUS: {llm}
LLM HAS NO HEALTH-DECISION AUTHORITY
LLM DOES NOT AUTHORIZE TICKET CREATION
DETERMINISTIC TICKETS EXIST BEFORE OPTIONAL PROSE ENRICHMENT

NETWORK
RUNTIME NETWORK DEPENDENCY: NONE

PROPRIETARY BOUNDARY
MODEL ALGORITHM IMPLEMENTATION AND PRIVATE CLASSIFIER COEFFICIENT ARRAYS ARE NOT DISPLAYED.
OPERATOR-FACING INPUTS, HEALTHY REFERENCE VALUES REQUIRED TO EXPLAIN CURRENT EVIDENCE,
PHYSICS CALIBRATION DATA, MODEL OUTPUTS, HEALTH STATE, DATA ORIGIN, AND AUTHORITY ARE VISIBLE.

RESEARCH LIMIT
DESIGN INFORMED BY INDUSTRIAL HMI, ALARM-DISPLAY, OT-SECURITY, AND ACCESSIBILITY GUIDANCE.
NO FORMAL CONFORMANCE OR CERTIFICATION IS CLAIMED.
""")
