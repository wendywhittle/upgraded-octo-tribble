"""Controlled evidence acquisition pipeline.

SOURCE -> NORMALIZE -> EVIDENCE -> INTEGRITY -> CORROBORATION.
Agent reasoning is intentionally outside this module.
"""

from datetime import datetime
from typing import Any, Dict

from app.evidence import validate_evidence
from app.evidence_sources import EvidenceSource, documents_to_evidence, corroboration_groups


def acquire_evidence(
    source: EvidenceSource,
    query: str,
    claim: str,
    limit: int = 10,
    now: datetime | None = None,
    max_age_seconds: float = 24 * 60 * 60,
) -> Dict[str, Any]:
    """Acquire, normalize, validate, and summarize evidence from a read-only source."""
    documents = list(source.acquire(query, limit=limit))
    evidence = documents_to_evidence(documents, claim=claim)
    validations = [
        validate_evidence(item, now=now, max_age_seconds=max_age_seconds)
        for item in evidence
    ]
    usable = [item for item, report in zip(evidence, validations) if report["decision_usable"]]

    return {
        "source": source.name,
        "query": query,
        "claim": claim,
        "document_count": len(documents),
        "evidence_count": len(evidence),
        "usable_evidence_count": len(usable),
        "decision_usable": bool(evidence) and len(usable) == len(evidence),
        "documents": [document.normalized() for document in documents],
        "evidence": evidence,
        "validation": validations,
        "corroboration": corroboration_groups(usable),
        "reasoning_applied": False,
        "execution_capability": False,
    }
