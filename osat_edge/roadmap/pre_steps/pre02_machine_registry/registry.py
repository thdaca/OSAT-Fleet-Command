"""The nine supported OSAT stations and their approved telemetry channels."""

from __future__ import annotations

from dataclasses import dataclass

from ..pre01_common.contracts import ChannelSpec


@dataclass(frozen=True)
class StationDefinition:
    family: str
    station_id: str
    name: str
    channels: tuple[ChannelSpec, ...]

    def __post_init__(self) -> None:
        names = [channel.name for channel in self.channels]
        source_ids = [channel.source_id for channel in self.channels]
        if len(names) != len(set(names)) or len(source_ids) != len(set(source_ids)):
            raise ValueError("Station channel names and source IDs must be unique")

    @property
    def subsystems(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(channel.subsystem for channel in self.channels))


def _channel(
    name: str,
    unit: str,
    subsystem: str,
    *,
    required: bool,
    period: float,
    source_id: str,
) -> ChannelSpec:
    return ChannelSpec(
        name=name,
        unit=unit,
        subsystem=subsystem,
        required=required,
        period_seconds=period,
        stale_seconds=max(3.0 * period, 5.0),
        source_id=source_id,
    )


STATIONS: dict[str, StationDefinition] = {
    "wafer_mount": StationDefinition(
        "wafer_mount", "WM-01", "Wafer Mount",
        (
            _channel("vacuum_pressure", "kPa", "vacuum", required=True, period=1, source_id="WM-SV-01"),
            _channel("roller_motor_current", "A", "motor", required=True, period=1, source_id="WM-SV-02"),
            _channel("roller_temperature", "°C", "thermal", required=False, period=10, source_id="WM-SV-03"),
            _channel("arm_tracking_error", "µm", "servo", required=False, period=1, source_id="WM-SV-04"),
            _channel("web_tension", "N", "feed", required=False, period=2, source_id="WM-SV-05"),
        ),
    ),
    "wafer_saw": StationDefinition(
        "wafer_saw", "WS-01", "Wafer Saw / Dicing",
        (
            _channel("spindle_current", "A", "spindle", required=True, period=1, source_id="WS-SV-01"),
            _channel("spindle_speed", "RPM", "spindle", required=True, period=1, source_id="WS-SV-02"),
            _channel("spindle_vibration", "mm/s", "spindle", required=False, period=0.5, source_id="WS-SV-03"),
            _channel("coolant_pressure", "MPa", "cooling", required=True, period=2, source_id="WS-SV-04"),
            _channel("coolant_flow", "L/min", "cooling", required=False, period=2, source_id="WS-SV-05"),
            _channel("feed_axis_error", "µm", "servo", required=False, period=1, source_id="WS-SV-06"),
            _channel("coolant_temperature", "°C", "thermal", required=False, period=10, source_id="WS-SV-07"),
        ),
    ),
    "die_attach": StationDefinition(
        "die_attach", "DA-01", "Die Attach",
        (
            _channel("nozzle_vacuum", "kPa", "vacuum", required=True, period=1, source_id="DA-SV-01"),
            _channel("z_axis_current", "A", "motor", required=True, period=1, source_id="DA-SV-02"),
            _channel("z_position_error", "µm", "servo", required=False, period=1, source_id="DA-SV-03"),
            _channel("stage_temperature", "°C", "thermal", required=False, period=10, source_id="DA-SV-04"),
            _channel("placement_settle_time", "ms", "motion", required=False, period=2, source_id="DA-SV-05"),
        ),
    ),
    "wire_bond": StationDefinition(
        "wire_bond", "WB-04", "Wire Bond",
        (
            _channel("bond_force", "gf", "bond_head", required=True, period=1, source_id="WB-SV-01"),
            _channel("bond_head_current", "A", "motor", required=True, period=1, source_id="WB-SV-02"),
            _channel("ultrasonic_current", "mA", "ultrasonic", required=False, period=1, source_id="WB-SV-03"),
            _channel("ultrasonic_frequency_shift", "Hz", "ultrasonic", required=False, period=2, source_id="WB-SV-04"),
            _channel("clamp_temperature", "°C", "thermal", required=False, period=10, source_id="WB-SV-05"),
        ),
    ),
    "molding": StationDefinition(
        "molding", "MO-01", "Molding",
        (
            _channel("cavity_pressure", "bar", "hydraulic", required=True, period=1, source_id="MO-SV-01"),
            _channel("transfer_motor_current", "A", "motor", required=True, period=1, source_id="MO-SV-02"),
            _channel("mold_temperature", "°C", "thermal", required=True, period=10, source_id="MO-SV-03"),
            _channel("clamp_pressure", "bar", "hydraulic", required=False, period=2, source_id="MO-SV-04"),
            _channel("plunger_position_error", "mm", "servo", required=False, period=1, source_id="MO-SV-05"),
        ),
    ),
    "marking": StationDefinition(
        "marking", "MK-01", "Laser Marking",
        (
            _channel("delivered_laser_power", "W", "optical", required=True, period=1, source_id="MK-SV-01"),
            _channel("laser_drive_current", "A", "optical", required=True, period=1, source_id="MK-SV-02"),
            _channel("laser_temperature", "°C", "thermal", required=False, period=10, source_id="MK-SV-03"),
            _channel("galvo_current", "A", "motor", required=False, period=1, source_id="MK-SV-04"),
            _channel("galvo_tracking_error", "µrad", "servo", required=False, period=1, source_id="MK-SV-05"),
        ),
    ),
    "trim_form": StationDefinition(
        "trim_form", "TF-01", "Trim / Form",
        (
            _channel("punch_force", "kN", "press", required=True, period=1, source_id="TF-SV-01"),
            _channel("press_motor_current", "A", "motor", required=True, period=1, source_id="TF-SV-02"),
            _channel("die_vibration", "mm/s", "press", required=False, period=0.5, source_id="TF-SV-03"),
            _channel("form_tracking_error", "µm", "servo", required=False, period=1, source_id="TF-SV-04"),
            _channel("die_temperature", "°C", "thermal", required=False, period=10, source_id="TF-SV-05"),
        ),
    ),
    "singulation": StationDefinition(
        "singulation", "SG-01", "Singulation",
        (
            _channel("blade_vibration", "mm/s", "spindle", required=True, period=0.5, source_id="SG-SV-01"),
            _channel("spindle_current", "A", "spindle", required=True, period=1, source_id="SG-SV-02"),
            _channel("spindle_speed", "RPM", "spindle", required=False, period=1, source_id="SG-SV-03"),
            _channel("coolant_flow", "L/min", "cooling", required=False, period=2, source_id="SG-SV-04"),
            _channel("feed_position_error", "µm", "servo", required=False, period=1, source_id="SG-SV-05"),
        ),
    ),
    "final_test": StationDefinition(
        "final_test", "FT-01", "Final Test",
        (
            _channel("contact_voltage_drop", "mV", "contacts", required=True, period=1, source_id="FT-SV-01"),
            _channel("site_current", "A", "contacts", required=True, period=1, source_id="FT-SV-02"),
            _channel("socket_temperature", "°C", "thermal", required=False, period=10, source_id="FT-SV-03"),
            _channel("handler_motor_current", "A", "motor", required=False, period=1, source_id="FT-SV-04"),
            _channel("handler_vibration", "g", "motion", required=False, period=0.5, source_id="FT-SV-05"),
        ),
    ),
}

STATION_ORDER = tuple(STATIONS)


def station_for_family(family: str) -> StationDefinition:
    try:
        return STATIONS[family]
    except KeyError as exc:
        raise ValueError(f"Unsupported machine family {family!r}") from exc
