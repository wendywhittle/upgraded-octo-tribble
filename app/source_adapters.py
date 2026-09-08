"""Read-only source adapters for AletheiaTelos.

Adapters acquire information only. They cannot execute trades, mutate accounts,
or bypass the evidence-integrity layer.
"""

from datetime import datetime, timezone
from typing import Iterable, List

from app.evidence_sources import EvidenceSource, SourceDocument


class StaticEvidenceSource:
    """Deterministic adapter used for tests and architecture demonstrations."""

    name = "static_demo"

    def __init__(self, documents: Iterable[SourceDocument]):
        self._documents = list(documents)

    def acquire(self, query: str, limit: int = 10) -> List[SourceDocument]:
        query_terms = {term.lower() for term in query.split() if term.strip()}
        matches = []
        for document in self._documents:
            haystack = f"{document.title} {document.content}".lower()
            if not query_terms or any(term in haystack for term in query_terms):
                matches.append(document)
            if len(matches) >= limit:
                break
        return matches


def source_status(source: EvidenceSource) -> dict:
    """Expose adapter capabilities without executing acquisition."""
    return {
        "name": source.name,
        "read_only": True,
        "execution_capability": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
