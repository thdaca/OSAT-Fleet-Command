"""Machine-family ownership for Step01 relations and research candidates."""

from __future__ import annotations

from ..core.schema import PhysicsRelation, RelationStatus, ResearchCandidate
from .wafer_mount import WAFER_MOUNT_CANDIDATE
from .wafer_saw import SPINDLE_RELATION, WAFER_SAW_CANDIDATE
from .die_attach import DIE_ATTACH_CANDIDATE
from .wire_bond import WIRE_BOND_CANDIDATE
from .molding import MOLDING_CANDIDATE
from .marking import MARKING_CANDIDATE
from .trim_form import TRIM_FORM_CANDIDATE
from .singulation import SINGULATION_CANDIDATE
from .final_test import FINAL_TEST_CANDIDATE


PHYSICS_RELATIONS: tuple[PhysicsRelation, ...] = (SPINDLE_RELATION,)

RESEARCH_CANDIDATES: tuple[ResearchCandidate, ...] = (
    WAFER_MOUNT_CANDIDATE,
    WAFER_SAW_CANDIDATE,
    DIE_ATTACH_CANDIDATE,
    WIRE_BOND_CANDIDATE,
    MOLDING_CANDIDATE,
    MARKING_CANDIDATE,
    TRIM_FORM_CANDIDATE,
    SINGULATION_CANDIDATE,
    FINAL_TEST_CANDIDATE,
)


ALL_MACHINE_FAMILIES: tuple[str, ...] = (
    "wafer_mount", "wafer_saw", "die_attach", "wire_bond", "molding",
    "marking", "trim_form", "singulation", "final_test",
)


def relations_for_family(family: str) -> tuple[PhysicsRelation, ...]:
    """Return runtime research relations only; Step 03 depends on this gate."""

    return tuple(relation for relation in PHYSICS_RELATIONS if relation.status is RelationStatus.RUNTIME_RESEARCH and family in relation.machine_families)


def research_catalog_for_family(family: str) -> tuple[PhysicsRelation | ResearchCandidate, ...]:
    runtime = relations_for_family(family)
    candidates = tuple(candidate for candidate in RESEARCH_CANDIDATES if candidate.family == family)
    return runtime + candidates

