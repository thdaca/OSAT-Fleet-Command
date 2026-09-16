"""OSAT Fleet Command 0.2.0 student research platform."""

from .common import (
    DataOrigin,
    EquipmentState,
    HealthState,
    RELEASE_CLASS,
    RuntimeMode,
    VERSION,
)
from .machines import STATIONS

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
