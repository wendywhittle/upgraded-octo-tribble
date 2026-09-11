from copy import deepcopy

import pytest

from app.capital_stack import CapitalSource, CapitalStack, DebtTerms, CapitalUse
from app.cre_simulation import CRESimulationConfig
from app.investment_case_assembly import (
    InvestmentCaseAssemblyValidationError,
    apply_assembly_to_case,
    assemble_investment_case,
)
from app.lender_intelligence import FinancingTerms, ProvenanceRecord
from app.proforma import ProFormaInput
from app.workflow import InvestmentCase


@pytest.fixture
def proforma_input() -> ProFormaInput:
    return ProFormaInput(
        asset_id="deal-001",
        acquisition_price=10_000_000,
        acquisition_costs=250_000,
        annual_rent=900_000,
        initial_occupancy=0.95,
        operating_expenses=180_000,
        rent_growth=0.03,
        expense_growth=0.03,
        entry_cap_rate=0.07,
        exit_cap_rate=0.07,
        projection_years=5,
    )


@pytest.fixture
def capital_stack() -> CapitalStack:
    return CapitalStack(
        sources=[
            CapitalSource(
                name="Senior Debt",
                source_type="DEBT",
                amount=6_000_000,
                debt_terms=DebtTerms(interest_rate=0.06, amortization_years=25, maturity_years=5),
            ),
            CapitalSource(name="Equity", source_type="EQUITY", amount=4_250_000),
        ],
        uses=[
            CapitalUse(name="Acquisition", use_type="ACQUISITION", amount=10_000_000),
            CapitalUse(name="Closing Costs", use_type="CLOSING_COSTS", amount=250_000),
        ],
    )


def lender_terms() -> FinancingTerms:
    return FinancingTerms(
        financing_id="fin-001",
        lender_id="lender-001",
        loan_type="Senior Permanent",
        minimum_loan=1_000_000,
        maximum_loan=15_000_000,
        maximum_ltv=0.75,
        minimum_dscr=1.25,
        interest_rate=0.06,
        rate_type="FIXED",
        amortization_years=25,
        maturity_years=5,
        recourse="LIMITED",
        provenance=[
            ProvenanceRecord(
                source="lender term sheet",
                observed_at="2026-09-11T00:00:00Z",
                freshness_status="CURRENT",
                verification_status="VERIFIED",
            )
        ],
    )


def test_end_to_end_assembly(proforma_input, capital_stack):
    result = assemble_investment_case(
        case_identity="deal-001",
        proforma_input=proforma_input,
        capital_stack=capital_stack,
        lender_terms=[lender_terms()],
        evidence=[
            {
                "evidence_id": "market-001",
                "claim": "Market rent is supported by current evidence",
                "status": "OBSERVED",
                "provenance": "SOURCE",
            }
        ],
        simulation_config=CRESimulationConfig(paths=100, seed=42),
    )

    assert result.case_identity == "deal-001"
    assert len(result.scenarios) == 4
    assert len(result.simulations) == 4
    assert result.financing is not None
    assert result.financing.output_types["debt_service_coverage_ratio"] == "CALCULATION"
    assert result.contrarian is not None
    assert result.synthesis.output_type == "INTERPRETATION"
    assert result.output_types["recommendation"] == "RECOMMENDATION"
    assert result.lender_terms[0].provenance[0].freshness_status == "CURRENT"


def test_assembly_is_deterministic(proforma_input, capital_stack):
    kwargs = dict(
        case_identity="deal-001",
        proforma_input=proforma_input,
        capital_stack=capital_stack,
        lender_terms=[lender_terms()],
        evidence=[{"evidence_id": "e1", "claim": "A sourced claim", "status": "OBSERVED"}],
        simulation_config=CRESimulationConfig(paths=100, seed=42),
    )
    first = assemble_investment_case(**kwargs)
    second = assemble_investment_case(**kwargs)
    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_calculation_and_interpretation_boundaries_are_preserved(proforma_input, capital_stack):
    result = assemble_investment_case(
        case_identity="deal-001",
        proforma_input=proforma_input,
        capital_stack=capital_stack,
        lender_terms=[lender_terms()],
        simulation_config=CRESimulationConfig(paths=100, seed=42),
    )
    assert result.proforma.output_types["unlevered_irr"] == "CALCULATION"
    assert all(r.proforma.output_types["unlevered_irr"] == "CALCULATION" for r in result.scenarios)
    assert all(r.output_types["probability_loss"] == "CALCULATION" for r in result.simulations)
    assert result.financing.output_types["loan_to_value"] == "CALCULATION"
    assert result.synthesis.output_type == "INTERPRETATION"
    assert result.output_types["recommendation"] == "RECOMMENDATION"


def test_lender_evidence_and_contradictions_remain_visible(proforma_input, capital_stack):
    term_a = lender_terms()
    term_b = term_a.model_copy(update={
        "financing_id": "fin-002",
        "maximum_ltv": 0.70,
        "conflict_status": "UNRESOLVED",
        "conflicting_financing_ids": ["fin-001"],
        "evidence_status": "CONTRADICTORY",
    })
    result = assemble_investment_case(
        case_identity="deal-001",
        proforma_input=proforma_input,
        capital_stack=capital_stack,
        lender_terms=[term_a, term_b],
        simulation_config=CRESimulationConfig(paths=100, seed=42),
    )
    assert len(result.lender_terms) == 2
    assert result.lender_terms[1].conflicting_financing_ids == ["fin-001"]
    assert any("contradictory" in item.lower() for item in result.synthesis.unresolved_questions)


def test_upstream_case_is_not_mutated(proforma_input, capital_stack):
    case = InvestmentCase(deal_id="deal-001", evidence=[{"evidence_id": "original"}])
    before = deepcopy(case.model_dump(mode="json"))
    result = assemble_investment_case(
        case_identity="deal-001",
        proforma_input=proforma_input,
        capital_stack=capital_stack,
        lender_terms=[lender_terms()],
        simulation_config=CRESimulationConfig(paths=100, seed=42),
    )
    updated = apply_assembly_to_case(case, result)
    assert case.model_dump(mode="json") == before
    assert updated is not case
    assert updated.deal_id == case.deal_id
    assert updated.workflow_state == case.workflow_state


def test_wrong_case_identity_is_rejected(proforma_input):
    with pytest.raises(InvestmentCaseAssemblyValidationError):
        assemble_investment_case(case_identity="other-deal", proforma_input=proforma_input)


def test_agent_calculation_cannot_become_authoritative(proforma_input):
    with pytest.raises(ValueError, match="authoritative calculated output"):
        assemble_investment_case(
            case_identity="deal-001",
            proforma_input=proforma_input,
            agent_perspectives=[{"agent_id": "quant", "unlevered_irr": 0.25}],
            simulation_config=CRESimulationConfig(paths=100, seed=42),
        )


def test_assembly_has_no_authorization_or_execution_surface(proforma_input):
    result = assemble_investment_case(
        case_identity="deal-001",
        proforma_input=proforma_input,
        simulation_config=CRESimulationConfig(paths=100, seed=42),
    )
    assert not hasattr(result, "authorize")
    assert not hasattr(result, "execute_transaction")
    assert not hasattr(result, "select_lender")
    assert result.recommendation != "PROCEED_TO_HUMAN_REVIEW" or result.status == "INVESTMENT_CASE"
