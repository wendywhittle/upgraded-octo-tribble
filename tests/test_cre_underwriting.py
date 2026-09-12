from app.cre_underwriting import CREUnderwritingRequest, underwrite_cre


def test_cre_underwriting_computes_core_metrics():
    result = underwrite_cre(
        CREUnderwritingRequest(
            purchase_price=1_000_000,
            annual_effective_gross_income=120_000,
            annual_operating_expenses=40_000,
            ltv=0.65,
            interest_rate=0.06,
            amortization_years=25,
            hold_years=5,
            exit_cap_rate=0.07,
        )
    )
    metrics = result["metrics"]
    assert metrics["noi"] == 80_000
    assert metrics["cap_rate"] == 0.08
    assert metrics["loan_amount"] == 650_000
    assert metrics["initial_equity"] == 350_000
    assert metrics["dscr"] > 1
    assert metrics["cash_on_cash"] is not None
    assert metrics["irr"] is not None
    assert metrics["equity_multiple"] is not None


def test_cre_underwriting_does_not_invent_missing_inputs():
    result = underwrite_cre(CREUnderwritingRequest())
    assert result["status"] == "INSUFFICIENT_INPUTS" or result["status"] == "PARTIAL"
    assert "noi" in result["unknown_metrics"]
    assert result["research_only"] is True
    assert result["investment_authority"] is False


def test_cre_router_exposes_underwriting_boundary():
    from app.cre_endpoint import build_cre_router

    paths = {route.path for route in build_cre_router().routes}
    assert "/cre/manifest" in paths
    assert "/cre/underwrite" in paths
