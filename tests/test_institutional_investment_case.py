from app.institutional_investment_case import (
    InvestmentCaseStatus,
    build_institutional_investment_case,
)
from app.decision_readiness import build_decision_readiness


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
        "Should this opportunity be investigated?", case_id="CASE-001", case_version=1,
        identity={"ticker": "EXAMPLE", "provider_id": "provider-1", "address": "1 Main St"},
        evidence_summary={"count": 1, "usable_count": 1, "validation": []}, decision_gate=gate(ready=True),
        synthesis={"verdict": "INVESTIGATE"}, governance=governance(),
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
        "Evaluate the opportunity", case_id="CASE-002", evidence=evidence,
        evidence_summary={"count": 1, "usable_count": 1, "validation": []}, perspectives=agents,
        conflicts=conflicts, risk=simulation, scenarios=simulation["scenarios"], contrarian_review=skeptic,
        decision_gate=gate(ready=True), synthesis={"verdict": "INVESTIGATE"}, governance=governance(),
    )
    assert case.evidence is evidence
    assert case.perspectives is agents
    assert case.conflicts is conflicts
    assert case.risk is simulation
    assert case.scenarios is simulation["scenarios"]
    assert case.contrarian_review is skeptic


def test_missing_evidence_becomes_insufficient_evidence_not_negative_evidence():
    case = build_institutional_investment_case(
        "Evaluate the opportunity", case_id="CASE-003", evidence_summary={"count": 0, "usable_count": 0, "validation": []},
        decision_gate=gate(ready=False), synthesis={"verdict": "NO_DATA"}, governance=governance(),
    )
    assert case.status == InvestmentCaseStatus.INSUFFICIENT_EVIDENCE
    assert case.status.value != "NEGATIVE_EVIDENCE"


def test_authority_boundary_is_not_embedded_as_execution_capability():
    case = build_institutional_investment_case(
        "Evaluate the opportunity", case_id="CASE-004", evidence_summary={"count": 1, "usable_count": 1, "validation": []},
        decision_gate=gate(ready=True), synthesis={"verdict": "INVESTIGATE"},
        governance={"autonomous_execution": True, "brokerage_connectivity": True, "portfolio_mutation": True, "investment_authority": True},
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
        "Evaluate the opportunity", case_id="CASE-005", case_version=1,
        evidence_summary={"count": 1, "usable_count": 1, "validation": []}, decision_gate=gate(ready=True), synthesis={"verdict": "INVESTIGATE"},
    )
    second = build_institutional_investment_case(
        "Evaluate the opportunity", case_id="CASE-005", case_version=2,
        evidence_summary={"count": 1, "usable_count": 1, "validation": []}, decision_gate=gate(ready=True), synthesis={"verdict": "INVESTIGATE"},
    )
    assert first.case_id == second.case_id == "CASE-005"
    assert first.case_version == 1
    assert second.case_version == 2


def test_capital_and_asset_domains_are_supported_without_domain_specific_models():
    capital = build_institutional_investment_case("Evaluate the security", case_id="CASE-CAPITAL", domain="capital", evidence_summary={"count": 1, "usable_count": 1, "validation": []}, decision_gate=gate(ready=False), synthesis={"verdict": "INVESTIGATE"})
    asset = build_institutional_investment_case("Evaluate the property", case_id="CASE-ASSET", domain="asset", evidence_summary={"count": 1, "usable_count": 1, "validation": []}, decision_gate=gate(ready=False), synthesis={"verdict": "INVESTIGATE"})
    assert capital.domain == "capital"
    assert asset.domain == "asset"
    assert capital.status == InvestmentCaseStatus.INVESTIGATE
    assert asset.status == InvestmentCaseStatus.INVESTIGATE


def test_decision_readiness_is_distinct_from_investment_case():
    case = build_institutional_investment_case(
        "Evaluate the opportunity", case_id="CASE-READINESS",
        evidence=[{"evidence_id": "E1", "source": "SEC", "claim": "fact", "provenance": {"uri": "x"}}],
        evidence_summary={"count": 1, "usable_count": 1, "validation": []},
        thesis={"statement": "explicit"}, assumptions=["assumption"], calculations={"value": 1},
        scenarios=[{"scenario": "bear"}, {"scenario": "adversarial"}],
        risk={"valid": True, "independent_of_agents": True, "scenarios": [{"scenario": "bear"}, {"scenario": "adversarial"}]},
        perspectives=[{"agent_id": p, "evidence_basis": ["E1"]} for p in ["researcher", "quant", "investor", "scientist", "systems", "skeptic", "contrarian", "governance"]],
        perspective_provenance=[{"agent_id": p, "independence_limitation": "shared inputs"} for p in ["researcher", "quant", "investor", "scientist", "systems", "skeptic", "contrarian", "governance"]],
        contrarian_review={"valid": True, "status": "reviewed", "challenges": ["challenge"]}, governance=governance(),
    )
    readiness = build_decision_readiness(case, evidence={"count": 1, "usable_count": 1, "validation": []}, simulation=case.risk, skeptic=case.contrarian_review, synthesis={"verdict": "INVESTIGATE"}, governance=governance())
    assert readiness is not case
    assert readiness["case_id"] == case.case_id
    assert readiness["status"] == "OPEN_READY_FOR_HUMAN_AUTHORITY"
    assert case.decision_readiness is None


def test_decision_readiness_preserves_missing_evidence_as_blocked():
    case = build_institutional_investment_case("Evaluate the opportunity", case_id="CASE-READINESS-NODATA", evidence_summary={"count": 0, "usable_count": 0, "validation": []}, synthesis={"verdict": "NO_DATA"}, governance=governance())
    readiness = build_decision_readiness(case, evidence={"count": 0, "usable_count": 0, "validation": []}, simulation={"valid": True}, skeptic={"valid": True}, synthesis={"verdict": "NO_DATA"}, governance=governance())
    assert case.status == InvestmentCaseStatus.INSUFFICIENT_EVIDENCE
    assert readiness["status"] == "CLOSED_BLOCKED"
    assert readiness["ready_for_human_authority"] is False
    assert "EVIDENCE_USABLE" in readiness["hard_stops"]


def test_pipeline_orders_case_then_readiness_then_gate(monkeypatch):
    import app.analysis_pipeline as pipeline
    order = []
    agent_stage = {"agents": [{"agent_id": "researcher", "direction": "LONG", "confidence": 0.5, "assumptions": []}], "evidence_count": 1, "usable_evidence_count": 1, "validation": [], "active_perspectives": ["researcher"], "reasoning_perspectives": ["researcher"], "registered_agent_count": 1, "provider": "test", "learning_context_supplied": False, "research_context_supplied": False, "perspectives_share_conclusions": False}
    conflict_data = {"conflicts": [], "horizon_divergences": []}
    simulation = {"valid": True, "scenarios": [{"name": "BASE"}]}
    skeptic = {"valid": True, "recommendation": "proceed_to_synthesis"}
    synthesis = {"verdict": "INVESTIGATE"}
    governance_output = governance()
    monkeypatch.setattr(pipeline, "read_records", lambda: [])
    monkeypatch.setattr(pipeline, "build_learning_report", lambda records: {})
    monkeypatch.setattr(pipeline, "run_evidence_fed_agents", lambda *args, **kwargs: agent_stage)
    monkeypatch.setattr(pipeline, "detect_conflicts", lambda agents: conflict_data)
    monkeypatch.setattr(pipeline, "run_monte_carlo", lambda *args, **kwargs: simulation)
    monkeypatch.setattr(pipeline, "skeptic_review", lambda *args, **kwargs: skeptic)
    monkeypatch.setattr(pipeline, "meta_intelligence_evaluate", lambda *args, **kwargs: {})
    monkeypatch.setattr(pipeline, "synthesize", lambda *args, **kwargs: synthesis)
    monkeypatch.setattr(pipeline, "build_kaleidoscope_view", lambda **kwargs: {"read_only": True})
    monkeypatch.setattr(pipeline, "observe", lambda *args, **kwargs: {})
    monkeypatch.setattr(pipeline, "build_record", lambda *args, **kwargs: {})
    monkeypatch.setattr(pipeline, "append_record", lambda record: None)
    real_case_builder = pipeline.build_institutional_investment_case
    real_readiness_builder = pipeline.build_decision_readiness
    real_gate_builder = pipeline.build_decision_gate
    def case_builder(*args, **kwargs): order.append("investment_case"); return real_case_builder(*args, **kwargs)
    def readiness_builder(*args, **kwargs): order.append("decision_readiness"); return real_readiness_builder(*args, **kwargs)
    def gate_builder(*args, **kwargs): order.append("decision_gate"); return real_gate_builder(*args, **kwargs)
    monkeypatch.setattr(pipeline, "build_institutional_investment_case", case_builder)
    monkeypatch.setattr(pipeline, "build_decision_readiness", readiness_builder)
    monkeypatch.setattr(pipeline, "build_decision_gate", gate_builder)
    result = pipeline.run_analysis("Evaluate the opportunity", [{"evidence_id": "E-1"}], paths=10)
    assert order == ["investment_case", "decision_readiness", "decision_gate"]
    assert result["institutional_investment_case"]["decision_readiness"]["status"] == "CLOSED_BLOCKED"
    assert result["decision_gate"]["ready_for_human_authority"] is False
