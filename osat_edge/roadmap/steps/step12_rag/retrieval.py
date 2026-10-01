"""Step 12: local TF-IDF retrieval over same-family guidance and prior work."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from ..step10_fault_evidence.evidence import FaultEvidence
from ..step11b_oem_manuals.manuals import ManualChunk, relevant_manuals


@dataclass(frozen=True)
class RetrievedPassage:
    source_id: str
    text: str


def retrieve_rag_context(
    evidence: FaultEvidence,
    maintenance_context: Sequence[str],
    manual_chunks: Sequence[ManualChunk],
    *,
    limit: int = 4,
) -> tuple[RetrievedPassage, ...]:
    if limit <= 0:
        return ()
    candidates = [
        RetrievedPassage(f"maintenance:{index}", text)
        for index, text in enumerate(maintenance_context)
        if text.strip()
    ]
    candidates.extend(
        RetrievedPassage(chunk.chunk_id, f"{chunk.title}. {chunk.text}")
        for chunk in relevant_manuals(manual_chunks, evidence)
    )
    if not candidates:
        return ()
    query = " ".join(
        (
            evidence.machine.name,
            evidence.machine.family,
            *evidence.suspected_subsystems,
            *evidence.evidence_descriptions,
        )
    )
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    try:
        matrix = vectorizer.fit_transform([candidate.text for candidate in candidates])
    except ValueError:
        return tuple(candidates[:limit])
    scores = (matrix @ vectorizer.transform([query]).T).toarray().reshape(-1)
    order = np.argsort(scores)[::-1][:limit]
    return tuple(candidates[int(index)] for index in order)
