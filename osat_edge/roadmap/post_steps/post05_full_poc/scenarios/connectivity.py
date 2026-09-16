"""Fixed loopback HSMS laboratory session, NOT a GEM stack or plant driver.

secsgem is imported only when this optional scenario executes. Its codecs
encode/decode the wire messages; the project owns only this fixed test session.
Fleet Command sends Select.rsp and report acknowledgments, never equipment
commands. RPTIDs in this authored fixture explicitly identify approved SVIDs.
"""
import datetime as dt
from importlib.metadata import version
from pathlib import Path
import socket
import struct

from .....pipeline import MachinePipeline
from ....pre_steps.pre01_common.pre01_common import DataOrigin, OperatingContext, EquipmentState
from ....pre_steps.pre01_common.core.authority import require_shadow_permission
from ....steps.step07_machine_model.core.model_io import identity_sha256
from ....steps.step08_live_telemetry.step08_live_telemetry import (
    QueuedTelemetrySource, SecsGemAdapter, TelemetryError, TelemetrySecurityError,
)
from ....steps.step11a_maintenance_db.step11a_maintenance_db import MaintenanceRepository
from ...post01_demo.post01_demo import SyntheticTelemetrySource, DEMO_START
from .onboarding import IDENTITY, STATION
from ..core.trace import store_identity


class SimulatorTelemetrySource(QueuedTelemetrySource):
    """Pass a rejected decode to the existing LIVE invalid-batch handler."""
    origin = DataOrigin.SYNTHETIC

    def __init__(self):
        super().__init__(IDENTITY, STATION)
        self.decode_error = None

    def poll(self):
        if self.decode_error is not None:
            message, self.decode_error = self.decode_error, None
            raise TelemetryError(message)
        return super().poll()


def _receive(connection):
    def exact(size):
        result = b""
        while len(result) < size:
            block = connection.recv(size - len(result))
            if not block:
                raise ConnectionError("Simulator session closed")
            result += block
        return result
    prefix = exact(4)
    length = struct.unpack(">I", prefix)[0]
    if not 10 <= length <= 65536:
        raise ValueError("Invalid simulator frame size")
    return prefix + exact(length)


def run_connectivity(workspace: Path):
    try:
        from secsgem.hsms import (HsmsBlock, HsmsSelectReqHeader, HsmsSelectRspHeader,
                                 HsmsStreamFunctionHeader)
        from secsgem.secs.functions import SecsS06F11, SecsS06F12
        from secsgem.secs.variables import F8
    except ImportError:
        return {"status": "NOT_RUN_OPTIONAL_DEPENDENCY_ABSENT", "required_dependency": "secsgem==0.3.0",
                "plant_interoperability_claimed": False}
    if version("secsgem") != "0.3.0":
        raise ValueError("PoC simulator requires pinned secsgem 0.3.0")
    source = SimulatorTelemetrySource()
    repository = MaintenanceRepository(workspace / "connectivity-tickets.sqlite")
    machine = MachinePipeline(identity=IDENTITY, station=STATION, source=source, repository=repository)
    adapter = SecsGemAdapter(IDENTITY, STATION)
    generator = SyntheticTelemetrySource(IDENTITY, STATION)
    transcript = []
    sent_by_host = []

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.settimeout(3)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        with socket.create_connection(listener.getsockname(), timeout=3) as equipment:
            host, _address = listener.accept()
            with host:
                host.settimeout(3)
                equipment.sendall(HsmsBlock(HsmsSelectReqHeader(1), b"").encode())
                selected = HsmsBlock.decode(_receive(host))
                if selected.header.s_type.value != 1:
                    raise ValueError("Expected HSMS Select.req")
                host.sendall(HsmsBlock(HsmsSelectRspHeader(selected.header.system), b"").encode())
                response = HsmsBlock.decode(_receive(equipment))
                if response.header.s_type.value != 2:
                    raise ValueError("Expected HSMS Select.rsp")
                sent_by_host.append("SELECT_RSP")

                def report(variables, now, system):
                    message = SecsS06F11({"DATAID": 1, "CEID": 101, "RPT": [
                        {"RPTID": source_id, "V": [F8(value) if type(value) in (float, int) else value]}
                        for source_id, value in variables
                    ]})
                    encoded = HsmsBlock(HsmsStreamFunctionHeader(system, 6, 11, True, 0), message.encode()).encode()
                    equipment.sendall(encoded)
                    raw = _receive(host)
                    decoded = HsmsBlock.decode(raw)
                    if (decoded.header.s_type.value, decoded.header.stream, decoded.header.function) != (0, 6, 11):
                        raise ValueError("Only S6F11 telemetry enters this simulator boundary")
                    message = SecsS06F11()
                    message.decode(decoded.data)
                    value = message.get()
                    if value["CEID"] != 101 or value["DATAID"] != 1:
                        raise TelemetrySecurityError("Unapproved simulated event")
                    payload = {"stream": 6, "function": 11, "variables": []}
                    for item in value["RPT"]:
                        if len(item["V"]) != 1:
                            raise TelemetryError("Simulator reports require exactly one SVID value")
                        payload["variables"].append({"id": item["RPTID"], "value": item["V"][0]})
                    accepted = True
                    try:
                        require_shadow_permission("telemetry_ingestion")
                        samples = adapter.parse(payload, received_at=now)
                        source.submit(samples, context=OperatingContext(IDENTITY.machine_id, now, EquipmentState.PROCESSING))
                    except (ValueError, TelemetrySecurityError) as exc:
                        accepted = False
                        source.decode_error = str(exc)
                    # An event ACK is a receipt, not an equipment-control command.
                    host.sendall(HsmsBlock(HsmsStreamFunctionHeader(system, 6, 12, False, 0),
                                          SecsS06F12(0 if accepted else 1).encode()).encode())
                    ack = HsmsBlock.decode(_receive(equipment))
                    if (ack.header.stream, ack.header.function) != (6, 12):
                        raise ValueError("Expected report acknowledgment only")
                    sent_by_host.append("S6F12")
                    transcript.append({"frame_hex": raw.hex(), "accepted": accepted})
                    return accepted

                for index in range(1, 81):
                    batch = generator.poll()
                    # S6F11 values here are explicitly latest-per-report, not a new
                    # synchronized telemetry contract in the inference path.
                    values = {s.source_id: s.value for s in batch.samples}
                    if not report(list(values.items()), batch.context.timestamp, index + 1):
                        raise ValueError("Approved simulator values rejected")
                    machine.tick(wall_now=batch.context.timestamp)
                observable_before_loss = machine.last_result.telemetry_status.observable
                before = store_identity(machine)
                now = DEMO_START + dt.timedelta(seconds=81)
                unmapped = not report([("UNMAPPED-SVID", 1.0)], now, 82)
                rejected_unmapped = machine.tick(wall_now=now)
                malformed = not report([(STATION.channels[0].source_id, "malformed")], now, 83)
                rejected_malformed = machine.tick(wall_now=now)
                rejected_invalid = not rejected_unmapped.telemetry_status.valid and not rejected_malformed.telemetry_status.valid
                unchanged = before == store_identity(machine)
                equipment.shutdown(socket.SHUT_RDWR)
                loss_detected = host.recv(1) == b""
                after = machine.tick(wall_now=now + dt.timedelta(seconds=120))
    passed = (observable_before_loss and unmapped and malformed and rejected_invalid and unchanged and loss_detected
              and not after.telemetry_status.valid and after.assessment.health_state.value == "UNKNOWN"
              and not repository.list_tickets())
    return {"status": "PASS" if passed else "FAIL", "transport": "LOOPBACK_TCP_HSMS_SELECT_S6F11",
            "dependency": "secsgem", "dependency_version": version("secsgem"), "license": "LGPL-2.1-or-later",
            "DataOrigin": "SYNTHETIC", "runtime_mode": "LIVE_EQUIPMENT",
            "connected_and_selected": True, "approved_reports": 80,
            "observable_before_loss": observable_before_loss, "unmapped_signals_rejected": unmapped,
            "malformed_values_rejected": malformed, "rejected_reports_store_unchanged": unchanged,
            "rejected_reports_telemetry_invalid": rejected_invalid,
            "session_loss_detected": loss_detected, "current_health_after_loss": after.assessment.health_state.value,
            "telemetry_after_loss": "INVALID" if not after.telemetry_status.valid else "VALID",
            "sent_by_fleet_command": sorted(set(sent_by_host)), "host_message_count": len(sent_by_host),
            "equipment_control_messages": 0, "operational_ticket_count": len(repository.list_tickets()),
            "transcript_sha256": identity_sha256(transcript), "plant_interoperability_claimed": False,
            "limitation": "Fixed authored report layout, not full GEM negotiation, OEM interoperability or plant validation; no REAL_OSAT-calibrated model."}
