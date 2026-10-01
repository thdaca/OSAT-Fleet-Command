"""Read-only equipment authority, separate from evidence/ticket eligibility."""

from enum import Enum


class AuthorityMode(str, Enum):
    SHADOW = "SHADOW / READ-ONLY"


SHADOW_ALLOWED = frozenset({"telemetry_ingestion", "health_assessment", "fault_evidence",
                            "maintenance_recommendation", "maintenance_ticket"})
SHADOW_FORBIDDEN = frozenset({"equipment_command", "shutdown", "recipe_change", "process_control"})


def require_shadow_permission(action: str) -> None:
    """Fail closed. Ticket permission still requires existing runtime/origin policy."""
    if action not in SHADOW_ALLOWED:
        raise PermissionError(f"{AuthorityMode.SHADOW.value} forbids {action}")
