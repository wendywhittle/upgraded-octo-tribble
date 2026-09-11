from fastapi.testclient import TestClient

from app.main import app
from app.phase9_visual import Phase9VisualRequest, assemble_visual_case


def request():
    return Phase9VisualRequest(
        asset_id="VISUAL-CRE-001",
        acquisition_price=10_000_000,
        acquisition_costs=250_000,
        annual_rent=850_000,
        other_income=25_000,
        initial_occupancy=0.95,
        vacancy_rate=0.02,
        rent_growth=0.03,
        operating_expenses=170_000,
        expense_growth=0.03,
        management_expense=20_000,
        property_tax=65_000,
        insurance=18_000,
        maintenance=15_000,
        utilities=8_000,
        capex=10_000,
        reserves=10_000,
        tenant_improvements=5_000,
        leasing_commissions=5_000,
        entry_cap_rate=0.06,
        exit_cap_rate=0.065,
        exit_costs=250_000,
        debt_amount=6_000_000,
        interest_rate=0.065,
        amortization_years=25,
        maturity_years=10,
        equity_contribution=4_250_000,
        simulation_paths=100,
        simulation_seed=42,
    )


def test_visual_boundary_uses_real_phase9_outputs_and_preserves_governance():
    result = assemble_visual_case(request())
    assembly = result["assembly"]
    assert assembly["proforma"]["output_types"]["unlevered_irr"] == "CALCULATION"
    assert len(assembly["scenarios"]) == 4
    assert len(assembly["simulations"]) == 4
    assert assembly["financing"]["output_types"]["debt_service_coverage_ratio"] == "CALCULATION"
    assert assembly["contrarian"] is not None
    assert assembly["synthesis"] is not None
    assert result["visual_integration"]["lender_evidence_status"] == "UNKNOWN / NOT PROVIDED"
    assert result["governance"] == {
        "human_authorization_required": True,
        "authorization_created": False,
        "workflow_mutated": False,
        "portfolio_created": False,
        "transaction_executed": False,
        "lender_selection_performed": False,
        "lender_evidence_provided": False,
    }


def test_visual_boundary_is_deterministic():
    assert assemble_visual_case(request()) == assemble_visual_case(request())


def test_visual_boundary_does_not_expose_authorization_controls():
    result = assemble_visual_case(request())
    assert "authorize" not in result
    assert "authorization" not in result["assembly"]
    assert "portfolio" not in result["assembly"]
    assert "transaction" not in result["assembly"]


def test_visual_http_boundary_returns_complete_phase9_payload_without_authority():
    response = TestClient(app).post("/phase9/visual", json=request().model_dump())
    assert response.status_code == 200
    payload = response.json()
    assert payload["assembly"]["case_identity"] == "VISUAL-CRE-001"
    assert len(payload["assembly"]["scenarios"]) == 4
    assert len(payload["assembly"]["simulations"]) == 4
    assert payload["assembly"]["proforma"]["output_types"]["unlevered_irr"] == "CALCULATION"
    assert payload["assembly"]["synthesis"]
    assert payload["governance"]["authorization_created"] is False
    assert payload["governance"]["workflow_mutated"] is False
    assert payload["visual_integration"]["lender_evidence_status"] == "UNKNOWN / NOT PROVIDED"


def test_visual_http_boundary_rejects_unknown_fields():
    body = request().model_dump()
    body["fake_probability"] = 0.99
    response = TestClient(app).post("/phase9/visual", json=body)
    assert response.status_code == 422
