from app.investment_domains import (
    AssetResearchDomain,
    CapitalResearchDomain,
    CrossAssetLink,
    IntelligenceEntity,
    InvestmentDomain,
    ResearchHypothesis,
    domain_manifest,
)


def test_manifest_exposes_capital_and_asset_engines():
    manifest = domain_manifest()
    assert "public_markets" in manifest["capital_engine"]
    assert "cre" in manifest["asset_engine"]
    assert "evidence_registry" in manifest["shared_layers"]
    assert manifest["execution_authority"] is False


def test_hypothesis_is_distinct_from_evidence():
    hypothesis = ResearchHypothesis(
        hypothesis_id="h-1",
        statement="Industrial expansion may increase regional demand.",
        domain=InvestmentDomain.CAPITAL,
        research_domains=[CapitalResearchDomain.PUBLIC_MARKETS.value],
        evidence_ids=["e-1"],
    )
    assert hypothesis.domain is InvestmentDomain.CAPITAL
    assert hypothesis.evidence_ids == ["e-1"]


def test_cross_asset_link_is_evidence_backed():
    company = IntelligenceEntity("company-1", "company", "Example Co")
    property_ = IntelligenceEntity("property-1", "property", "Example Industrial Park")
    link = CrossAssetLink(company, "capital_expenditure_supports", property_, ["e-1"])
    assert link.from_entity.entity_type == "company"
    assert link.to_entity.entity_type == "property"
    assert link.evidence_ids == ["e-1"]
    assert AssetResearchDomain.INDUSTRIAL.value == "industrial"
