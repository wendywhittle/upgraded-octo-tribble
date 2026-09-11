from dataclasses import dataclass

from app.capital_engine import AlternativeDataRegistry, CapitalResearchRequest, capital_engine_manifest
from app.evidence_sources import SourceDocument
from app.investment_domains import CapitalResearchDomain


@dataclass
class FakeProvider:
    name: str = "fake"

    def acquire(self, query: str, limit: int = 10):
        assert query == "industrial expansion"
        return [
            SourceDocument(
                source=self.name,
                title="Observed activity",
                content="Industrial expansion announced.",
                retrieved_at="2026-09-11T00:00:00+00:00",
                observed_at="2026-09-10T00:00:00+00:00",
                source_id="e-1",
                point_in_time=True,
            )
        ][:limit]


def test_registry_has_no_required_provider():
    registry = AlternativeDataRegistry()
    assert registry.names() == []
    packet = registry.acquire(CapitalResearchRequest("anything"))
    assert packet.documents == []
    assert packet.execution_authority is False


def test_registry_accepts_provider_without_making_it_authoritative():
    registry = AlternativeDataRegistry([FakeProvider()])
    request = CapitalResearchRequest(
        "industrial expansion",
        domains=[CapitalResearchDomain.ALTERNATIVE_DATA],
    )
    packet = registry.acquire(request)
    assert packet.provider_names == ["fake"]
    assert packet.documents[0].source == "fake"
    assert packet.execution_authority is False


def test_duplicate_provider_names_are_rejected():
    registry = AlternativeDataRegistry([FakeProvider()])
    try:
        registry.register(FakeProvider())
    except ValueError as exc:
        assert "already registered" in str(exc)
    else:
        raise AssertionError("duplicate provider should be rejected")


def test_capital_manifest_is_research_only():
    manifest = capital_engine_manifest()
    assert manifest["provider_agnostic"] is True
    assert manifest["quiver_role"] == "optional_alternative_data_provider"
    assert manifest["execution"]["order_submission"] is False
    assert manifest["execution"]["portfolio_mutation"] is False
