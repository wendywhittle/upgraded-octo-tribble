"""Structured, auditable CRE underwriting primitives and first-pass economics."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

from .cre_financial_model import break_even_exit_cap, break_even_occupancy, debt_service, irr, max_loan_for_dscr, max_purchase_price_for_cap, remaining_balance


class UnderwritingDecision(str, Enum):
    ACT = "ACT"
    WATCH = "WATCH"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT EVIDENCE"
    NO_DEAL = "NO DEAL"


class InputStatus(str, Enum):
    OBSERVED = "OBSERVED"
    ASSUMED = "ASSUMED"
    DERIVED = "DERIVED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Property:
    property_id: str
    asset_type: str
    market: str
    rentable_area: float | None = None
    occupancy: float | None = None
    year_built: int | None = None
    tenant_count: int | None = None
    tenant_concentration: float | None = None
    lease_type: str | None = None
    remaining_lease_term_years: float | None = None


@dataclass(frozen=True)
class Assumption:
    name: str
    value: float | str
    unit: str
    source: str | None = None
    evidence_id: str | None = None
    confidence: float | None = None
    invalidation_condition: str | None = None
    status: InputStatus = InputStatus.ASSUMED

    def __post_init__(self) -> None:
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("assumption confidence must be between 0 and 1")


@dataclass(frozen=True)
class UnderwritingInputs:
    opportunity_id: str
    property: Property
    purchase_price: float | None
    annual_noi: float | None
    assumptions: Sequence[Assumption] = field(default_factory=tuple)
    evidence_ids: Sequence[str] = field(default_factory=tuple)
    contradictory_evidence: Sequence[str] = field(default_factory=tuple)
    uncertainty_notes: Sequence[str] = field(default_factory=tuple)
    no_deal_reasons: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class UnderwritingResult:
    decision: UnderwritingDecision
    going_in_cap_rate: float | None
    reasons: Sequence[str] = field(default_factory=tuple)
    missing_inputs: Sequence[str] = field(default_factory=tuple)
    fragile_assumptions: Sequence[str] = field(default_factory=tuple)
    invalidation_conditions: Sequence[str] = field(default_factory=tuple)
    evidence_ids: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class CREFinancialInputs:
    """Explicit property economics. None means UNKNOWN, never an implied default."""
    purchase_price: float | None
    noi: float | None
    gross_rent: float | None = None
    effective_income: float | None = None
    occupancy: float | None = None
    vacancy: float | None = None
    operating_expenses: float | None = None
    rent_growth: float | None = None
    expense_growth: float | None = None
    capital_expenditures: float | None = None
    loan_amount: float | None = None
    loan_to_value: float | None = None
    interest_rate: float | None = None
    amortization_years: int | None = None
    interest_only: bool = False
    hold_period_years: int | None = None
    exit_cap_rate: float | None = None
    selling_cost_rate: float | None = None
    closing_costs: float | None = None
    other_income: float | None = None
    lease_term_years: float | None = None
    rent_escalation: float | None = None
    renewal_probability: float | None = None
    tenant_concentration: float | None = None
    tenant_credit_quality: str | None = None
    rollover_year: int | None = None
    downtime_years: float | None = None
    leasing_costs: float | None = None
    tenant_improvements: float | None = None
    evidence_ids: Sequence[str] = field(default_factory=tuple)
    assumptions: Sequence[Assumption] = field(default_factory=tuple)


@dataclass(frozen=True)
class CREFinancialResult:
    status: str
    input_status: dict[str, InputStatus]
    missing_inputs: Sequence[str] = field(default_factory=tuple)
    going_in_cap_rate: float | None = None
    equity_requirement: float | None = None
    annual_debt_service: float | None = None
    dscr: float | None = None
    debt_yield: float | None = None
    cash_on_cash: float | None = None
    exit_value: float | None = None
    net_sale_proceeds: float | None = None
    equity_multiple: float | None = None
    irr: float | None = None
    projected_noi: Sequence[float] = field(default_factory=tuple)
    projected_cash_flow: Sequence[float] = field(default_factory=tuple)
    annual_equity_values: Sequence[float] = field(default_factory=tuple)
    break_even_occupancy: float | None = None
    break_even_exit_cap: float | None = None
    max_purchase_price_at_target_cap: float | None = None
    max_loan_at_target_dscr: float | None = None
    evidence_ids: Sequence[str] = field(default_factory=tuple)


def _status_for(name: str, value: object, assumptions: Sequence[Assumption], derived: set[str]) -> InputStatus:
    if name in derived:
        return InputStatus.DERIVED
    if value is None:
        return InputStatus.UNKNOWN
    for assumption in assumptions:
        if assumption.name == name:
            return assumption.status
    if name in {"rent_growth", "expense_growth", "exit_cap_rate", "selling_cost_rate", "renewal_probability"}:
        return InputStatus.ASSUMED
    return InputStatus.OBSERVED


def underwrite_financial_model(inputs: CREFinancialInputs) -> CREFinancialResult:
    """Calculate transparent CRE economics from explicit inputs only."""
    missing: list[str] = []
    required_values = {
        "purchase_price": inputs.purchase_price,
        "noi": inputs.noi,
        "hold_period_years": inputs.hold_period_years,
        "exit_cap_rate": inputs.exit_cap_rate,
        "rent_growth": inputs.rent_growth,
        "expense_growth": inputs.expense_growth,
        "capital_expenditures": inputs.capital_expenditures,
        "selling_cost_rate": inputs.selling_cost_rate,
    }
    for name, value in required_values.items():
        if value is None or (isinstance(value, (int, float)) and value <= 0 and name in {"purchase_price", "noi", "hold_period_years", "exit_cap_rate"}):
            missing.append(name)
    if inputs.loan_amount is None and inputs.loan_to_value is None:
        missing.append("loan_to_value")
    if inputs.capital_expenditures is not None and inputs.capital_expenditures < 0:
        missing.append("capital_expenditures")
    if inputs.selling_cost_rate is not None and not 0 <= inputs.selling_cost_rate < 1:
        missing.append("selling_cost_rate")
    derived: set[str] = set()
    if inputs.effective_income is None and inputs.gross_rent is not None and (inputs.occupancy is not None or inputs.vacancy is not None): derived.add("effective_income")
    if inputs.loan_amount is None and inputs.loan_to_value is not None and inputs.purchase_price is not None: derived.add("loan_amount")
    fields = {"purchase_price": inputs.purchase_price, "noi": inputs.noi, "gross_rent": inputs.gross_rent, "effective_income": inputs.effective_income, "occupancy": inputs.occupancy, "vacancy": inputs.vacancy, "operating_expenses": inputs.operating_expenses, "rent_growth": inputs.rent_growth, "expense_growth": inputs.expense_growth, "capital_expenditures": inputs.capital_expenditures, "loan_amount": inputs.loan_amount, "loan_to_value": inputs.loan_to_value, "interest_rate": inputs.interest_rate, "amortization_years": inputs.amortization_years, "exit_cap_rate": inputs.exit_cap_rate, "selling_cost_rate": inputs.selling_cost_rate, "closing_costs": inputs.closing_costs, "lease_term_years": inputs.lease_term_years, "rent_escalation": inputs.rent_escalation, "renewal_probability": inputs.renewal_probability}
    status = {name: _status_for(name, value, inputs.assumptions, derived) for name, value in fields.items()}
    if missing: return CREFinancialResult("INSUFFICIENT EVIDENCE", status, tuple(dict.fromkeys(missing)), evidence_ids=tuple(inputs.evidence_ids))

    price, noi, hold = float(inputs.purchase_price), float(inputs.noi), int(inputs.hold_period_years)
    cap = noi / price
    loan = inputs.loan_amount if inputs.loan_amount is not None else price * float(inputs.loan_to_value)
    if loan < 0: return CREFinancialResult("INSUFFICIENT EVIDENCE", status, ("loan_amount",), going_in_cap_rate=cap, evidence_ids=tuple(inputs.evidence_ids))
    equity = price + float(inputs.closing_costs or 0.0) - loan
    annual_ds = None
    if loan > 0:
        if inputs.interest_rate is None: return CREFinancialResult("INSUFFICIENT EVIDENCE", status, ("interest_rate",), going_in_cap_rate=cap, equity_requirement=equity, evidence_ids=tuple(inputs.evidence_ids))
        annual_ds = debt_service(loan, inputs.interest_rate, inputs.amortization_years, inputs.interest_only)
        if annual_ds is None: return CREFinancialResult("INSUFFICIENT EVIDENCE", status, ("amortization_years",), going_in_cap_rate=cap, equity_requirement=equity, evidence_ids=tuple(inputs.evidence_ids))

    projected_noi: list[float] = []; projected_cash_flow: list[float] = []; annual_equity_values: list[float] = []; current_noi = noi
    for year in range(1, hold + 1):
        if inputs.gross_rent is not None and inputs.operating_expenses is not None and (inputs.occupancy is not None or inputs.vacancy is not None):
            income = inputs.gross_rent * (1 + inputs.rent_growth) ** year
            vacancy = inputs.vacancy if inputs.vacancy is not None else 1 - float(inputs.occupancy)
            income = income * max(0.0, 1 - vacancy) + float(inputs.other_income or 0.0)
            expenses = inputs.operating_expenses * (1 + inputs.expense_growth) ** year
            current_noi = income - expenses
        else:
            current_noi = current_noi * (1 + inputs.rent_growth)
        projected_noi.append(current_noi)
        projected_cash_flow.append(current_noi - float(annual_ds or 0.0) - float(inputs.capital_expenditures))
        balance = remaining_balance(loan, inputs.interest_rate if inputs.interest_rate is not None else 0.0, inputs.amortization_years, year, inputs.interest_only)
        annual_equity_values.append(current_noi / inputs.exit_cap_rate - balance)

    exit_value = projected_noi[-1] / float(inputs.exit_cap_rate)
    net_sale = exit_value * (1 - float(inputs.selling_cost_rate)) - remaining_balance(loan, inputs.interest_rate if inputs.interest_rate is not None else 0.0, inputs.amortization_years, hold, inputs.interest_only)
    cash_on_cash = projected_cash_flow[0] / equity if equity > 0 else None
    equity_multiple = (sum(projected_cash_flow) + net_sale) / equity if equity > 0 else None
    irr_value = irr([-equity, *projected_cash_flow[:-1], projected_cash_flow[-1] + net_sale]) if equity > 0 else None
    dscr_value = noi / annual_ds if annual_ds and annual_ds > 0 else None
    debt_yield_value = noi / loan if loan > 0 else None
    break_occ = break_even_occupancy(inputs.gross_rent, inputs.operating_expenses, annual_ds or 0.0, inputs.capital_expenditures, inputs.other_income or 0.0) if inputs.gross_rent is not None and inputs.operating_expenses is not None else None
    break_exit = break_even_exit_cap(projected_noi[-1], equity, inputs.selling_cost_rate) if equity > 0 else None
    target_cap = next((float(a.value) for a in inputs.assumptions if a.name == "target_cap_rate" and isinstance(a.value, (int, float))), None)
    target_dscr = next((float(a.value) for a in inputs.assumptions if a.name == "minimum_dscr" and isinstance(a.value, (int, float))), None)
    max_price = max_purchase_price_for_cap(noi, target_cap) if target_cap is not None else None
    max_loan = max_loan_for_dscr(noi, target_dscr, inputs.interest_rate, inputs.amortization_years, inputs.interest_only) if target_dscr is not None and inputs.interest_rate is not None else None
    return CREFinancialResult("CALCULATED", status, (), cap, equity, annual_ds, dscr_value, debt_yield_value, cash_on_cash, exit_value, net_sale, equity_multiple, irr_value, tuple(projected_noi), tuple(projected_cash_flow), tuple(annual_equity_values), break_occ, break_exit, max_price, max_loan, tuple(inputs.evidence_ids))


def underwrite(inputs: UnderwritingInputs) -> UnderwritingResult:
    """Perform deterministic first-pass underwriting without inventing inputs."""
    missing = []
    if not inputs.opportunity_id.strip(): missing.append("opportunity_id")
    if not inputs.property.asset_type.strip(): missing.append("property.asset_type")
    if not inputs.property.market.strip(): missing.append("property.market")
    if inputs.purchase_price is None or inputs.purchase_price <= 0: missing.append("purchase_price")
    if inputs.annual_noi is None or inputs.annual_noi < 0: missing.append("annual_noi")
    if missing: return UnderwritingResult(UnderwritingDecision.INSUFFICIENT_EVIDENCE, None, ("Required underwriting inputs are missing or invalid.",), tuple(missing), evidence_ids=tuple(inputs.evidence_ids))
    cap_rate = inputs.annual_noi / inputs.purchase_price
    fragile = tuple(a.name for a in inputs.assumptions if a.confidence is not None and a.confidence < 0.6)
    invalidations = tuple(a.invalidation_condition for a in inputs.assumptions if a.invalidation_condition)
    reasons = [f"Going-in cap rate: {cap_rate:.2%}"]
    if inputs.contradictory_evidence: reasons.append("Contradictory evidence is present and requires review.")
    if inputs.uncertainty_notes: reasons.append("Material uncertainty has been recorded.")
    if fragile: reasons.append("One or more assumptions have low recorded confidence.")
    if inputs.no_deal_reasons:
        reasons.extend(inputs.no_deal_reasons)
        return UnderwritingResult(UnderwritingDecision.NO_DEAL, cap_rate, tuple(reasons), fragile_assumptions=fragile, invalidation_conditions=invalidations, evidence_ids=tuple(inputs.evidence_ids))
    return UnderwritingResult(UnderwritingDecision.WATCH, cap_rate, tuple(reasons), fragile_assumptions=fragile, invalidation_conditions=invalidations, evidence_ids=tuple(inputs.evidence_ids))
