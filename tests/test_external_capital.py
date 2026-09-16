import pytest

from app.external_capital import (
    DEFAULT_EXTERNAL_CAPITAL_REGISTRY,
    ExternalCapitalProvider,
    ExternalCapitalRegistry,
    PRIDECO_LOANS,
)


def test_prideco_is_external_and_has_no_authority():
    provider = DEFAULT_EXTERNAL_CAPITAL_REGISTRY.get("prideco_loans")

    assert provider is PRIDECO_LOANS
    assert provider.name == "PrideCo Loans"
    assert provider.relationship == "external"
    assert provider.authority == "none"
    assert provider.decision_authority is False
    assert provider.execution_authority is False
    assert provider.portfolio_authority is False
    assert provider.investment_approval_authority is False
    assert provider.data_access == "none"
    assert provider.financing_observations == "unvalidated_until_evidence_boundary"


def test_registry_is_provider_independent():
    registry = ExternalCapitalRegistry()
    provider = ExternalCapitalProvider(
        provider_id="future_provider",
        name="Future Provider",
        category="External Capital Provider",
        role="Capital-market information source",
    )

    registry.register(provider)

    assert [item.provider_id for item in registry.list()] == ["future_provider"]
    assert registry.manifest()["provider_agnostic"] is True
    assert registry.manifest()["execution_capability"] is False
    assert registry.manifest()["investment_authority"] is False


def test_registry_rejects_non_external_relationship():
    registry = ExternalCapitalRegistry()
    provider = ExternalCapitalProvider(
        provider_id="invalid",
        name="Invalid",
        category="External Capital Provider",
        role="Test",
        relationship="internal",
    )

    with pytest.raises(ValueError, match="relationship='external'"):
        registry.register(provider)


def test_registry_rejects_authority_flags():
    registry = ExternalCapitalRegistry()
    provider = ExternalCapitalProvider(
        provider_id="invalid-authority",
        name="Invalid Authority",
        category="External Capital Provider",
        role="Test",
        execution_authority=True,
    )

    with pytest.raises(ValueError, match="cannot receive system authority"):
        registry.register(provider)
