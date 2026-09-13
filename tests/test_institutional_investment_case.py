from app.institutional_investment_case import (
    InvestmentCaseStatus,
    build_institutional_investment_case,
)


def gate(ready=False):
    return {
        "state": "OPEN_READY_FOR_HUMAN_AUTHORITY" if ready else "CLOSED_BLOCKED",
        "ready_for_human_authority": ready,
        "human_decision": None,
        "human_authorization": None,
        "approval": None,
        "research_only": True,
    }


def governance():
    return {
        "human_decision_required": True,
        "autonomous_execution": False,
        "brokerage_connectivity": False,
        "portfolio_mutation": False,
        "investment_authority": False,
    }


def test_case_identity_is_explicit_and_independent_of_external_identifiers():
    case = build_institutional_investment_case(
        "Should this opportunity be investigated?",
        case_id="CASE-001",
        case_version=1,
        identity={"ticker": "EXAMPLE", "provider_id": "provider-1", "address": "1 Main St"},
        evidence_summary={"count": 1, "usable_count": 1, "validation": []},
        decision_gate=gate(ready=True),
        synthesis={"verdict": "INVESTIGATE"},
        governance=governance(),
    )
    assert case.case_id == "CASE-001"
    assert case.case_version == 1
    assert case.status == InvestmentCaseStatus.READY_FOR_HUMAN_AUTHORITY
    assert case.ready_for_human_authority is True


def test_assembly_preserves_existing_analytical_outputs():
    evidence = [{"evidence_id": "E-1", "source": "primary", "claim": "Observed fact"}]
    agents = [{"agent_id": "researcher", "direction": "LONG"}]
    conflicts = {"conflicts": [{"conflict_type": "valuation"}], "horizon_divergences": []}
    simulation = {"valid": True, "scenarios": [{"name": "BASE"}]}
    skeptic = {"status": "reviewed", "recommendation": "proceed_to_synthesis"}
    case = build_institutional_investment_case(
        "Evaluate the opportunity",
        case_id="CASE-002",
        evidence=evidence,
        evidence_summary={"count": 1, "usable_count": 1, "validation": []},
        perspectives=agents,
        conflicts=conflicts,
        risk=simulation,
        scenarios=simulation["scenarios"],
        contrarian_review=skeptic,
        decision_gate=gate(ready=True),
        synthesis={"verdict": "INVESTIGATE"},
        governance=governance(),
    )
    assert case.evidence is evidence
    assert case.perspectives is agents
    assert case.conflicts is conflicts
    assert case.risk is simulation
    assert case.scenarios is simulation["scenarios"]
    assert case.contrarian_review is skeptic


def test_missing_evidence_becomes_insufficient_evidence_not_negative_evidence():
    case = build_institutional_investment_case(
        "Evaluate the opportunity",
        case_id="CASE-003",
        evidence_summary={"count": 0, "usable_count": 0, "validation": []},
        decision_gate=gate(ready=False),
        synthesis={"verdict": "NO_DATA"},
        governance=governance(),
    )
    assert case.status == InvestmentCaseStatus.INSUFFICIENT_EVIDENCE
    assert case.status.value != "NEGATIVE_EVIDENCE"


def test_authority_boundary_is_not_embedded_as_execution_capability():
    case = build_institutional_investment_case(
        "Evaluate the opportunity",
        case_id="CASE-004",
        evidence_summary={"count": 1, "usable_count": 1, "validation": []},
        decision_gate=gate(ready=True),
        synthesis={"verdict": "INVESTIGATE"},
        governance={
            "autonomous_execution": True,
            "brokerage_connectivity": True,
            "portfolio_mutation": True,
            "investment_authority": True,
        },
    )
    projected = case.to_dict()
    assert projected["status"] == "READY_FOR_HUMAN_AUTHORITY"
    assert projected["human_authorization"] is None
    assert projected["authorized"] is False
    assert projected["executed"] is False
    assert case.governance["autonomous_execution"] is False
    assert case.governance["brokerage_connectivity"] is False
    assert case.governance["portfolio_mutation"] is False
    assert case.governance["investment_authority"] is False


def test_versioning_keeps_case_id_stable_while_version_changes():
    first = build_institutional_investment_case(
        "Evaluate the opportunity",
        case_id="CASE-005",
        case_version=1,
        evidence_summary={"count": 1, "usable_count": 1, "validation": []},
        decision_gate=gate(ready=True),
        synthesis={"verdict": "INVESTIGATE"},
    )
    second = build_institutional_investment_case(
        "Evaluate the opportunity",
        case_id="CASE-005",
        case_version=2,
        evidence_summary={"count": 1, "usable_count": 1, "validation": []},
        decision_gate=gate(ready=True),
        synthesis={"verdict": "INVESTIGATE"},
    )
    assert first.case_id == second.case_id == "CASE-005"
    assert first.case_version == 1
    assert second.case_version == 2


def test_capital_and_asset_domains_are_supported_without_domain_specific_models():
    capital = build_institutional_investment_case(
        "Evaluate the security",
        case_id="CASE-CAPITAL",
        domain="capital",
        evidence_summary={"count": 1, "usable_count": 1, "validation": []},
        decision_gate=gate(ready=False),
        synthesis={"verdict": "INVESTIGATE"},
    )
    asset = build_institutional_investment_case(
        "Evaluate the property",
        case_id="CASE-ASSET",
        domain="asset",
        evidence_summary={"count": 1, "usable_count": 1, "validation": []},
        decision_gate=gate(ready=False),
        synthesis={"verdict": "INVESTIGATE"},
    )
    assert capital.domain == "capital"
    assert asset.domain == "asset"
    assert capital.status == InvestmentCaseStatus.INVESTIGATE
    assert asset.status == InvestmentCaseStatus.INVESTIGATE
