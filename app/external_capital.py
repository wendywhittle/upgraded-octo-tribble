"""Provider-independent external capital ecosystem primitives.

External capital providers are represented as read-only ecosystem participants.
Their public or supplied financing information may become evidence only after
passing the existing evidence/provenance validation boundary.

This module intentionally contains no lending, underwriting, execution,
capital-transfer, brokerage, portfolio-mutation, or investment-authority
capability.
"""

from dataclasses import asdict, dataclass, field
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class ExternalCapitalProvider:
    """Descriptive record for an external capital-market participant."""

    provider_id: str
    name: str
    category: str
    role: str
    relationship: str = "external"
    primary_relevance: List[str] = field(default_factory=list)
    authority: str = "none"
    decision_authority: bool = False
    execution_authority: bool = False
    portfolio_authority: bool = False
    investment_approval_authority: bool = False
    data_access: str = "none"
    financing_observations: str = "unvalidated_until_evidence_boundary"

    def normalized(self) -> Dict[str, object]:
        """Return a stable, UI/API-safe representation of the provider."""
        return asdict(self)


class ExternalCapitalRegistry:
    """Small provider-independent registry with no privileged providers."""

    def __init__(self, providers: Iterable[ExternalCapitalProvider] = ()) -> None:
        self._providers: Dict[str, ExternalCapitalProvider] = {}
        for provider in providers:
            self.register(provider)

    def register(self, provider: ExternalCapitalProvider) -> None:
        provider_id = provider.provider_id.strip()
        if not provider_id:
            raise ValueError("External capital provider_id must not be empty.")
        if provider_id in self._providers:
            raise ValueError(f"External capital provider already registered: {provider_id}")
        if provider.relationship != "external":
            raise ValueError("External capital ecosystem providers must have relationship='external'.")
        if any((provider.decision_authority, provider.execution_authority,
                provider.portfolio_authority, provider.investment_approval_authority)):
            raise ValueError("External capital providers cannot receive system authority.")
        self._providers[provider_id] = provider

    def get(self, provider_id: str) -> ExternalCapitalProvider:
        return self._providers[provider_id]

    def list(self) -> List[ExternalCapitalProvider]:
        return [self._providers[key] for key in sorted(self._providers)]

    def manifest(self) -> Dict[str, object]:
        return {
            "subsystem": "external_capital_ecosystem",
            "provider_agnostic": True,
            "research_only": True,
            "execution_capability": False,
            "investment_authority": False,
            "financing_commitment_capability": False,
            "capital_transfer_capability": False,
            "providers": [provider.normalized() for provider in self.list()],
            "evidence_boundary": "external_observation -> provenance -> validation -> validated_evidence",
        }


PRIDECO_LOANS = ExternalCapitalProvider(
    provider_id="prideco_loans",
    name="PrideCo Loans",
    category="External Capital Provider / Private Real-Estate Lender",
    role="Potential financing counterparty and capital-market information source",
    primary_relevance=["real-estate financing", "private lending", "capital structure"],
)


DEFAULT_EXTERNAL_CAPITAL_REGISTRY = ExternalCapitalRegistry([PRIDECO_LOANS])
