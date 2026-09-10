"""Structured, auditable CRE underwriting primitives and first-pass economics."""
from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Sequence


class UnderwritingDecision(str, Enum):
    ACT = "ACT"
    WATCH = "WATCH"
    REJECT = "REJECT"
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
        if self.value is None:
            raise ValueError("assumption value cannot be None")


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
    """Explicit first-pass property economics. Unknown values remain None."""
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
    hold_period_years: int | None = None
    exit_cap_rate: float | None = None
    selling_cost_rate: float | None = None
    closing_costs: float | None = None
    other_income: float | None = None
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
    evidence_ids: Sequence[str] = field(default_factory=tuple)


def _debt_service(principal: float, annual_rate: float, amortization_years: int | None) -> float | None:
    if principal <= 0:
        return 0.0
    if amortization_years is None or amortization_years <= 0:
        return None
    if annual_rate < 0:
        return None
    if annual_rate == 0:
        return principal / amortization_years
    r = annual_rate / 12
    n = amortization_years * 12
    payment = principal * r / (1 - (1 + r) ** -n)
    return payment * 12


def _remaining_balance(principal: float, annual_rate: float, amortization_years: int, years_elapsed: int) -> float:
    if principal <= 0:
        return 0.0
    if annual_rate == 0:
        return max(0.0, principal * (1 - years_elapsed / amortization_years))
    r = annual_rate / 12
    n = amortization_years * 12
    k = min(n, years_elapsed * 12)
    payment = principal * r / (1 - (1 + r) ** -n)
    return max(0.0, principal * (1 + r) ** k - payment * ((1 + r) ** k - 1) / r)


def _irr(cash_flows: Sequence[float]) -> float | None:
    if not cash_flows or not (any(v > 0 for v in cash_flows) and any(v < 0 for v in cash_flows)):
        return None
    low, high = -0.9999, 10.0
    def npv(rate: float) -> float:
        return sum(value / ((1 + rate) ** period) for period, value in enumerate(cash_flows))
    if npv(low) * npv(high) > 0:
        return None
    for _ in range(120):
        mid = (low + high) / 2
        value = npv(mid)
        if abs(value) < 1e-7:
            return mid
        if npv(low) * value <= 0:
            high = mid
        else:
            low = mid
    return (low + high) / 2


def underwrite_financial_model(inputs: CREFinancialInputs) -> CREFinancialResult:
    """Calculate transparent CRE economics from explicit inputs only."""
    missing: list[str] = []
    if inputs.purchase_price is None or inputs.purchase_price <= 0:
        missing.append("purchase_price")
    if inputs.noi is None or inputs.noi < 0:
        missing.append("noi")
    if inputs.hold_period_years is None or inputs.hold_period_years <= 0:
        missing.append("hold_period_years")
    if inputs.exit_cap_rate is None or inputs.exit_cap_rate <= 0:
        missing.append("exit_cap_rate")

    status = {
        "purchase_price": InputStatus.OBSERVED if inputs.purchase_price is not None else InputStatus.UNKNOWN,
        "noi": InputStatus.OBSERVED if inputs.noi is not None else InputStatus.UNKNOWN,
        "gross_rent": InputStatus.OBSERVED if inputs.gross_rent is not None else InputStatus.UNKNOWN,
        "effective_income": InputStatus.OBSERVED if inputs.effective_income is not None else InputStatus.UNKNOWN,
        "occupancy": InputStatus.OBSERVED if inputs.occupancy is not None else InputStatus.UNKNOWN,
        "operating_expenses": InputStatus.OBSERVED if inputs.operating_expenses is not None else InputStatus.UNKNOWN,
        "rent_growth": InputStatus.ASSUMED if inputs.rent_growth is not None else InputStatus.UNKNOWN,
        "expense_growth": InputStatus.ASSUMED if inputs.expense_growth is not None else InputStatus.UNKNOWN,
        "exit_cap_rate": InputStatus.ASSUMED if inputs.exit_cap_rate is not None else InputStatus.UNKNOWN,
    }
    if missing:
        return CREFinancialResult("INSUFFICIENT EVIDENCE", status, tuple(missing), evidence_ids=tuple(inputs.evidence_ids))

    price = float(inputs.purchase_price)
    noi = float(inputs.noi)
    hold = int(inputs.hold_period_years)
    cap = noi / price
    loan = inputs.loan_amount
    if loan is None and inputs.loan_to_value is not None:
        loan = price * inputs.loan_to_value
        status["loan_amount"] = InputStatus.DERIVED
    if loan is not None and loan < 0:
        missing.append("loan_amount")
    equity = price + (inputs.closing_costs or 0.0) - (loan or 0.0)

    debt_service = None
    if loan is not None:
        if inputs.interest_rate is None or inputs.amortization_years is None:
            missing.extend(name for name in ("interest_rate", "amortization_years") if getattr(inputs, name) is None)
        else:
            debt_service = _debt_service(loan, inputs.interest_rate, inputs.amortization_years)
            if debt_service is None:
                missing.append("debt_service")
    if missing:
        return CREFinancialResult("INSUFFICIENT EVIDENCE", status, tuple(dict.fromkeys(missing)), going_in_cap_rate=cap, evidence_ids=tuple(inputs.evidence_ids))

    rent_growth = inputs.rent_growth or 0.0
    expense_growth = inputs.expense_growth or 0.0
    current_noi = noi
    projected_noi: list[float] = []
    projected_cash_flow: list[float] = []
    annual_equity_values: list[float] = []
    for year in range(1, hold + 1):
        if inputs.gross_rent is not None and inputs.operating_expenses is not None:
            gross = inputs.gross_rent * (1 + rent_growth) ** year
            occ = inputs.occupancy if inputs.occupancy is not None else 1.0
            vacancy = inputs.vacancy if inputs.vacancy is not None else max(0.0, 1 - occ)
            income = gross * max(0.0, 1 - vacancy)
            expenses = inputs.operating_expenses * (1 + expense_growth) ** year
            current_noi = max(0.0, income + (inputs.other_income or 0.0) - expenses)
        else:
            current_noi *= 1 + rent_growth
        projected_noi.append(current_noi)
        debt_cf = debt_service or 0.0
        projected_cash_flow.append(current_noi - debt_cf - (inputs.capital_expenditures or 0.0))
        remaining_debt = _remaining_balance(loan or 0.0, inputs.interest_rate or 0.0, inputs.amortization_years or 1, year) if loan else 0.0
        annual_equity_values.append(max(0.0, current_noi / inputs.exit_cap_rate - remaining_debt))

    exit_value = projected_noi[-1] / float(inputs.exit_cap_rate)
    selling_costs = exit_value * (inputs.selling_cost_rate or 0.0)
    remaining_debt = _remaining_balance(loan or 0.0, inputs.interest_rate or 0.0, inputs.amortization_years or 1, hold) if loan else 0.0
    net_sale = exit_value - selling_costs - remaining_debt
    cash_on_cash = projected_cash_flow[0] / equity if equity > 0 else None
    total_distributions = sum(projected_cash_flow) + net_sale
    equity_multiple = total_distributions / equity if equity > 0 else None
    irr = _irr([-equity, *projected_cash_flow[:-1], projected_cash_flow[-1] + net_sale])
    dscr = noi / debt_service if debt_service and debt_service > 0 else None
    debt_yield = noi / loan if loan and loan > 0 else None
    return CREFinancialResult(
        "CALCULATED", status, (), cap, equity, debt_service, dscr, debt_yield,
        cash_on_cash, exit_value, net_sale, equity_multiple, irr,
        tuple(projected_noi), tuple(projected_cash_flow), tuple(annual_equity_values), tuple(inputs.evidence_ids),
    )


def underwrite(inputs: UnderwritingInputs) -> UnderwritingResult:
    """Perform deterministic first-pass underwriting without inventing inputs."""
    missing: list[str] = []
    if not inputs.opportunity_id.strip():
        missing.append("opportunity_id")
    if not inputs.property.asset_type.strip():
        missing.append("property.asset_type")
    if not inputs.property.market.strip():
        missing.append("property.market")
    if inputs.purchase_price is None or inputs.purchase_price <= 0:
        missing.append("purchase_price")
    if inputs.annual_noi is None or inputs.annual_noi < 0:
        missing.append("annual_noi")

    if missing:
        return UnderwritingResult(UnderwritingDecision.INSUFFICIENT_EVIDENCE, None, ("Required underwriting inputs are missing or invalid.",), tuple(missing), evidence_ids=tuple(inputs.evidence_ids))

    assert inputs.purchase_price is not None
    assert inputs.annual_noi is not None
    cap_rate = inputs.annual_noi / inputs.purchase_price
    fragile = tuple(a.name for a in inputs.assumptions if a.confidence is not None and a.confidence < 0.6)
    invalidations = tuple(a.invalidation_condition for a in inputs.assumptions if a.invalidation_condition)
    reasons = [f"Going-in cap rate: {cap_rate:.2%}"]
    if inputs.contradictory_evidence:
        reasons.append("Contradictory evidence is present and requires review.")
    if inputs.uncertainty_notes:
        reasons.append("Material uncertainty has been recorded.")
    if fragile:
        reasons.append("One or more assumptions have low recorded confidence.")
    if inputs.no_deal_reasons:
        reasons.extend(inputs.no_deal_reasons)
        return UnderwritingResult(UnderwritingDecision.NO_DEAL, cap_rate, tuple(reasons), fragile_assumptions=fragile, invalidation_conditions=invalidations, evidence_ids=tuple(inputs.evidence_ids))
    return UnderwritingResult(UnderwritingDecision.WATCH, cap_rate, tuple(reasons), fragile_assumptions=fragile, invalidation_conditions=invalidations, evidence_ids=tuple(inputs.evidence_ids))
