"""Capital Engine boundary for public-market and alternative-data research.

The Capital Engine is intentionally research-only. Providers supply normalized
source documents; the engine exposes research structure but never places orders,
mutates portfolios, or treats provider output as an investment decision.
"""

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from app.evidence_sources import EvidenceSource, SourceDocument
from app.investment_domains import CapitalResearchDomain, InvestmentDomain, ResearchHypothesis


@dataclass(frozen=True)
class CapitalResearchRequest:
    question: str
    domains: List[CapitalResearchDomain] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class CapitalResearchPacket:
    """Provider-neutral input packet for the existing evidence/reasoning pipeline."""

    request: CapitalResearchRequest
    documents: List[SourceDocument]
    provider_names: List[str]
    hypotheses: List[ResearchHypothesis] = field(default_factory=list)

    @property
    def execution_authority(self) -> bool:
        return False


class AlternativeDataRegistry:
    """Small provider registry; no provider is required at application startup."""

    def __init__(self, sources: Iterable[EvidenceSource] = ()) -> None:
        self._sources: Dict[str, EvidenceSource] = {}
        for source in sources:
            self.register(source)

    def register(self, source: EvidenceSource) -> None:
        name = str(source.name).strip()
        if not name:
            raise ValueError("Evidence source name must not be empty.")
        if name in self._sources:
            raise ValueError(f"Evidence source already registered: {name}")
        self._sources[name] = source

    def names(self) -> List[str]:
        return sorted(self._sources)

    def acquire(self, request: CapitalResearchRequest, limit: int = 10) -> CapitalResearchPacket:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        documents: List[SourceDocument] = []
        providers: List[str] = []
        for name, source in self._sources.items():
            providers.append(name)
            documents.extend(source.acquire(request.question, limit=limit))
        return CapitalResearchPacket(
            request=request,
            documents=documents,
            provider_names=providers,
        )


def capital_engine_manifest() -> Dict[str, object]:
    """Describe the Capital Engine without exposing execution capabilities."""
    return {
        "domain": InvestmentDomain.CAPITAL.value,
        "research_domains": [item.value for item in CapitalResearchDomain],
        "provider_agnostic": True,
        "quiver_role": "optional_alternative_data_provider",
        "execution": {
            "brokerage_connectivity": False,
            "order_submission": False,
            "portfolio_mutation": False,
            "investment_authority": False,
        },
        "downstream": [
            "evidence_validation",
            "computational_kaleidoscope",
            "conflict_coexistence",
            "independent_simulation",
            "contrarian_review",
            "human_investment_committee",
            "epistemic_memory",
        ],
    }
