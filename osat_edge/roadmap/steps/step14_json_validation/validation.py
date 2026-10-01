"""Step 14: tiny explicit validation for optional LLM ticket prose."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from ..step10_fault_evidence.evidence import FaultEvidence
from ..step12_rag.retrieval import RetrievedPassage


_BIDI_CONTROLS = frozenset(
    "\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"
)


@dataclass(frozen=True)
class TicketEnrichment:
    summary: str
    likely_issue: str
    recommended_checks: tuple[str, ...]
    backend: str


def _clean(value: Any, limit: int) -> str:
    text = "".join(
        character
        for character in str(value)
        if (
            (unicodedata.category(character) != "Cc" or character in "\t\n\r")
            and character not in _BIDI_CONTROLS
        )
    )
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", " ", text)
    return re.sub(r"\s+", " ", text).strip()[:limit]


def deterministic_fallback(
    evidence: FaultEvidence,
    passages: Sequence[RetrievedPassage],
) -> TicketEnrichment:
    localized = ", ".join(evidence.suspected_subsystems) or "unlocalized machine-wide evidence"
    checks = tuple(
        f"Review approved local guidance: {_clean(passage.text, 220)}"
        for passage in passages[:3]
        if _clean(passage.text, 220)
    )
    if not checks:
        checks = tuple(
            f"Inspect the {subsystem} subsystem using approved maintenance procedures."
            for subsystem in evidence.suspected_subsystems[:3]
        ) or ("Review deterministic evidence with qualified maintenance personnel.",)
    return TicketEnrichment(
        summary=(
            f"{evidence.health_state.value} equipment-health transition for "
            f"{evidence.machine.station_id}."
        ),
        likely_issue=(
            f"Contributing evidence is associated with {localized}; this is not causal proof."
        ),
        recommended_checks=checks,
        backend="deterministic-fallback",
    )


def validate_llm_json(
    raw: str | None,
    evidence: FaultEvidence,
    passages: Sequence[RetrievedPassage],
) -> TicketEnrichment:
    fallback = deterministic_fallback(evidence, passages)
    if raw is None:
        return fallback
    try:
        payload = json.loads(raw)
        if not isinstance(payload, Mapping):
            return fallback
        if set(payload) != {"summary", "likely_issue", "recommended_checks"}:
            return fallback
        checks = payload["recommended_checks"]
        if not isinstance(checks, list) or not 1 <= len(checks) <= 6:
            return fallback
        fields = [payload["summary"], payload["likely_issue"], *checks]
        if any(not isinstance(value, str) or not value.strip() for value in fields):
            return fallback
        summary = _clean(payload["summary"], 500)
        likely_issue = _clean(payload["likely_issue"], 500)
        cleaned_checks = tuple(_clean(value, 280) for value in checks)
        if not summary or not likely_issue or any(not value for value in cleaned_checks):
            return fallback
        return TicketEnrichment(
            summary=summary,
            likely_issue=likely_issue,
            recommended_checks=cleaned_checks,
            backend="local-llm",
        )
    except (TypeError, ValueError, json.JSONDecodeError):
        return fallback
