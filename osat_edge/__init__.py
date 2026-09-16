"""OSAT Fleet Command student research platform."""

from .roadmap.pre_steps.pre01_common import (
    DataOrigin,
    EquipmentState,
    HealthState,
    RELEASE_CLASS,
    RuntimeMode,
    VERSION,
)
from .roadmap.pre_steps.pre02_machine_registry import STATIONS

__all__ = [
    "DataOrigin",
    "EquipmentState",
    "HealthState",
    "RELEASE_CLASS",
    "RuntimeMode",
    "STATIONS",
    "VERSION",
]

__version__ = VERSION
