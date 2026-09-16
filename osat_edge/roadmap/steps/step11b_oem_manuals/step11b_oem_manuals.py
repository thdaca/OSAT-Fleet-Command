"""Step 11B: local demo playbooks standing in for future OEM manuals."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from ..step10_fault_evidence.step10_fault_evidence import FaultEvidence


DEFAULT_MANUALS_PATH = (
    Path(__file__).resolve().parent
    / "resources"
    / "maintenance_playbooks.json"
)


@dataclass(frozen=True)
class ManualChunk:
    chunk_id: str
    family: str
    subsystem: str | None
    title: str
    text: str


def load_oem_manuals(path: str | Path = DEFAULT_MANUALS_PATH) -> tuple[ManualChunk, ...]:
    """Load local research guidance; bundled playbooks are not OEM-certified."""

    source = Path(path)
    if not source.is_file():
        return ()
    raw = json.loads(source.read_text(encoding="utf-8"))
    chunks: list[ManualChunk] = []
    for item in raw.get("chunks", []):
        chunks.append(
            ManualChunk(
                chunk_id=str(item["id"]),
                family=str(item.get("station_key", "fleet")),
                subsystem=(str(item["subsystem"]) if item.get("subsystem") else None),
                title=str(item["title"]),
                text="RESEARCH/DEMO GUIDANCE — " + str(item["body"]),
            )
        )
    return tuple(chunks)


def relevant_manuals(
    chunks: Sequence[ManualChunk],
    evidence: FaultEvidence,
) -> tuple[ManualChunk, ...]:
    allowed_families = {evidence.machine.family, "fleet"}
    suspected = set(evidence.suspected_subsystems)
    return tuple(
        chunk
        for chunk in chunks
        if chunk.family in allowed_families
        and (chunk.subsystem is None or not suspected or chunk.subsystem in suspected)
    )
