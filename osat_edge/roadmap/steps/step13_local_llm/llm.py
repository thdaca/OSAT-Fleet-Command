"""Step 13: optional local llama.cpp/GGUF explanation only."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from ..step10_fault_evidence.evidence import FaultEvidence
from ..step12_rag.retrieval import RetrievedPassage


def generate_local_llm_json(
    evidence: FaultEvidence,
    passages: Sequence[RetrievedPassage],
    *,
    model_path: str | Path | None = None,
) -> str | None:
    if model_path is None:
        return None
    path = Path(model_path).expanduser().resolve()
    if path.suffix.lower() != ".gguf" or not path.is_file():
        return None
    try:
        from llama_cpp import Llama
    except ImportError:
        return None
    sanitized = {
        "machine_id": evidence.machine.machine_id,
        "family": evidence.machine.family,
        "health_state": evidence.health_state.value,
        "suspected_subsystems": list(evidence.suspected_subsystems),
        "evidence_descriptions": list(evidence.evidence_descriptions),
        "family_risk_note": evidence.family_risk_note,
        "local_passages": [passage.text for passage in passages],
    }
    prompt = (
        "Return strict JSON with exactly summary, likely_issue, and recommended_checks. "
        "Explain only the supplied deterministic evidence. Do not change health, create "
        "or suppress a ticket, or invent measurements.\n"
        + json.dumps(sanitized, ensure_ascii=False, sort_keys=True)
    )
    try:
        model = Llama(
            model_path=str(path),
            n_ctx=2048,
            n_threads=1,
            n_gpu_layers=0,
            verbose=False,
        )
        response = model.create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=400,
            response_format={"type": "json_object"},
        )
        return str(response["choices"][0]["message"]["content"])
    except Exception:
        return None
