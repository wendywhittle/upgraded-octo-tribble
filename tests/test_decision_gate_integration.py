from unittest.mock import patch

from app.analysis_endpoint import AnalysisRequest, build_analysis_router


NOW_CRE_CONTEXT = {
    "opportunity_id": "cre-integration-1",
    "property_id": "prop-integration-1",
    "asset_type": "industrial",
    "location": "Vancouver, WA",
    "purchase_price": 10_000_000,
    "noi": 700_000,
    "occupancy": 0.95,
    "rent_growth": 0.03,
    "expense_growth": 0.02,
    "vacancy": 0.05,
    "interest_rate": 0.06,
    "hold_period": 5,
    "capital_expenditures": 25_000,
    "evidence": ("E-1",),
    "assumptions": ("normalized NOI",),
    "exit_assumptions": {"exit_cap_rate": 0.07, "selling_cost_rate": 0.02, "closing_costs": 0.0},
    "financing_assumptions": {"loan_to_value": 0.65, "amortization_years": 25},
}


def evidence():
    return [{
        "evidence_id": "E-1",
        "source": "integration-test-source",
        "claim": "The observed condition is material.",
        "observed_at": "2026-09-08T11:00:00+00:00",
        "retrieved_at": "2026-09-08T11:05:00+00:00",
        "provenance": {"type": "primary", "point_in_time": True},
    }]


def analysis_endpoint():
    router = build_analysis_router()
    return next(route.endpoint for route in router.routes if route.path == "/analysis/run")


def test_real_analysis_workflow_reaches_decision_gate():
    request = AnalysisRequest(
        question="Assess CRE opportunity",
        evidence=evidence(),
        paths=100,
        cre_context=NOW_CRE_CONTEXT,
    )
    with patch("app.analysis_pipeline.append_record"), patch("app.analysis_endpoint.append_record"):
        result = analysis_endpoint()(request)

    gate = result["decision_gate"]
    assert gate["state"] in {"OPEN", "CLOSED"}
    assert set(gate["readiness_criteria"]) == {
        "OPPORTUNITY_DEFINED",
        "EVIDENCE_INTEGRITY",
        "UNDERWRITING_COMPLETE",
        "MULTI_PERSPECTIVE_CHALLENGE_COMPLETE",
        "CONTRARIAN_REVIEW_COMPLETE",
        "SCENARIO_ANALYSIS_COMPLETE",
        "CONFLICTS_CHARACTERIZED",
        "MATERIAL_UNKNOWNS_CLASSIFIED",
        "GOVERNANCE_CHECK_PASSED",
        "DECISION_RECORD_COMPLETE",
    }
    assert gate["system_can_authorize"] is False
    assert "human_decision" not in gate
    assert result["cre"]["decision"].human_decision_required is True


def test_real_workflow_fails_closed_when_cre_evidence_is_missing():
    request = AnalysisRequest(
        question="Assess CRE opportunity",
        evidence=[],
        paths=100,
        cre_context=NOW_CRE_CONTEXT,
    )
    with patch("app.analysis_pipeline.append_record"), patch("app.analysis_endpoint.append_record"):
        result = analysis_endpoint()(request)

    gate = result["decision_gate"]
    assert gate["state"] == "CLOSED"
    assert gate["readiness_criteria"]["EVIDENCE_INTEGRITY"] == "FAIL"
    assert "CRITICAL_EVIDENCE_GAP" in gate["hard_stops"]
    assert gate["system_can_authorize"] is False


def test_integrated_gate_keeps_recommendation_separate_from_human_decision():
    request = AnalysisRequest(
        question="Assess CRE opportunity",
        evidence=evidence(),
        paths=100,
        cre_context=NOW_CRE_CONTEXT,
    )
    with patch("app.analysis_pipeline.append_record"), patch("app.analysis_endpoint.append_record"):
        result = analysis_endpoint()(request)

    gate = result["decision_gate"]
    assert "system_recommendation" in gate
    assert "human_decision" not in gate
    assert "human_decision" not in result
