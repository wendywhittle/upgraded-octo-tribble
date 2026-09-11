from app.investment_domains import (
    AssetResearchDomain,
    CapitalResearchDomain,
    CrossAssetLink,
    IntelligenceEntity,
    InvestmentDomain,
    ResearchHypothesis,
    classify_cross_asset_links,
    cross_asset_hypotheses,
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


def test_unbacked_cross_asset_link_remains_a_hypothesis():
    company = IntelligenceEntity("company-1", "company", "Example Co")
    property_ = IntelligenceEntity("property-1", "property", "Example Industrial Park")
    link = CrossAssetLink(company, "may_drive_demand_for", property_, ["missing-evidence"])

    classified = classify_cross_asset_links([link], evidence_ids=[])[0]

    assert classified["evidence_backed"] is False
    assert classified["epistemic_stage"] == "hypothesis"
    assert classified["missing_evidence_ids"] == ["missing-evidence"]


def test_backed_cross_asset_link_is_explicitly_evidence():
    company = IntelligenceEntity("company-1", "company", "Example Co")
    property_ = IntelligenceEntity("property-1", "property", "Example Industrial Park")
    link = CrossAssetLink(company, "capital_expenditure_supports", property_, ["e-1"])

    classified = classify_cross_asset_links([link], evidence_ids=["e-1"])[0]

    assert classified["evidence_backed"] is True
    assert classified["epistemic_stage"] == "evidence"
    assert classified["missing_evidence_ids"] == []


def test_cross_asset_relationship_generates_testable_hypothesis():
    company = IntelligenceEntity("company-1", "company", "Example Co")
    property_ = IntelligenceEntity(
        "property-1", "industrial_asset", "Example Industrial Park", "Pacific Northwest"
    )
    link = CrossAssetLink(company, "drives_demand_for", property_, ["e-1"])

    hypotheses = cross_asset_hypotheses([link], ["e-1"])

    assert len(hypotheses) == 1
    assert hypotheses[0].domain is InvestmentDomain.ASSET
    assert hypotheses[0].evidence_ids == ["e-1"]
    assert hypotheses[0].statement == (
        "Example Co may drives demand for Example Industrial Park in Pacific Northwest."
    )
    assert hypotheses[0].invalidation_conditions
    assert hypotheses[0].research_questions
    assert "confirm or falsify" in hypotheses[0].research_questions[0]
