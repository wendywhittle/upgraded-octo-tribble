"""Provider-agnostic evidence acquisition and provenance primitives.

This layer deliberately stops at acquisition/normalization. It does not make
investment decisions and it does not require a particular web, news, or market
provider. Providers can implement ``EvidenceSource`` and return normalized
``SourceDocument`` objects for downstream validation and reasoning.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import re
from typing import Any, Dict, Iterable, List, Optional, Protocol
from urllib.parse import urlparse


def _utc(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def content_fingerprint(content: str) -> str:
    """Return a stable SHA-256 fingerprint for acquired source content."""
    normalized = re.sub(r"\s+", " ", content or "").strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def normalize_source_identity(source: str, url: Optional[str] = None) -> str:
    """Normalize a source identity so duplicate/syndicated copies can be grouped."""
    if url:
        parsed = urlparse(url)
        host = (parsed.netloc or "").lower().removeprefix("www.")
        if host:
            return host
    return re.sub(r"[^a-z0-9]+", "-", (source or "unknown").lower()).strip("-") or "unknown"


@dataclass(frozen=True)
class SourceDocument:
    source: str
    title: str
    content: str
    retrieved_at: str
    observed_at: Optional[str] = None
    url: Optional[str] = None
    source_id: Optional[str] = None
    provenance_type: str = "external"
    point_in_time: bool = False
    source_identity: Optional[str] = None
    content_hash: Optional[str] = None

    def normalized(self) -> Dict[str, Any]:
        source_identity = self.source_identity or normalize_source_identity(self.source, self.url)
        return {
            **asdict(self),
            "source_identity": source_identity,
            "content_hash": self.content_hash or content_fingerprint(self.content),
        }


class EvidenceSource(Protocol):
    """Contract implemented by external evidence providers."""

    name: str

    def acquire(self, query: str, limit: int = 10) -> Iterable[SourceDocument]:
        ...


def documents_to_evidence(documents: Iterable[SourceDocument], claim: str) -> List[Dict[str, Any]]:
    """Convert normalized source documents into evidence records."""
    evidence: List[Dict[str, Any]] = []
    for index, document in enumerate(documents, start=1):
        item = document.normalized()
        evidence.append({
            "evidence_id": item.get("source_id") or f"evidence-{index}-{item['content_hash'][:12]}",
            "source": item["source"],
            "claim": claim,
            "observed_at": item.get("observed_at"),
            "retrieved_at": item["retrieved_at"],
            "provenance": {
                "type": item["provenance_type"],
                "point_in_time": item["point_in_time"],
                "source_identity": item["source_identity"],
                "content_hash": item["content_hash"],
                "url": item.get("url"),
                "title": item.get("title"),
            },
        })
    return evidence


def corroboration_groups(evidence: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group evidence by claim and content/source identity without overstating independence."""
    groups: Dict[str, Dict[str, Any]] = {}
    for item in evidence:
        provenance = item.get("provenance") or {}
        claim_key = re.sub(r"\s+", " ", str(item.get("claim", "")).strip().lower())
        source_identity = provenance.get("source_identity") or normalize_source_identity(item.get("source", ""), provenance.get("url"))
        content_hash = provenance.get("content_hash") or content_fingerprint(str(item.get("claim", "")))
        key = f"{claim_key}|{content_hash}"
        group = groups.setdefault(key, {"claim": item.get("claim"), "content_hash": content_hash, "sources": [], "independent_source_count": 0})
        if source_identity not in group["sources"]:
            group["sources"].append(source_identity)
            if provenance.get("independent", True) is not False:
                group["independent_source_count"] += 1
    return list(groups.values())
