"""Provider-independent capital-structure analysis.

This module analyzes explicitly supplied, validated financing evidence. It does
not approve financing, select providers, rank structures, execute transactions,
or grant investment authority.
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple


class ValueClassification(str, Enum):
    OBSERVED = "observed"
    DERIVED = "derived"
    ASSUMED = "assumed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class AnalyticalValue:
    """A value whose epistemic origin remains explicit."""

    value: Any = None
    classification: ValueClassification = ValueClassification.UNKNOWN
    source_evidence_ids: Tuple[str, ...] = field(default_factory=tuple)
    assumption: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_evidence_ids", tuple(self.source_evidence_ids))
        if self.classification == ValueClassification.OBSERVED and not self.source_evidence_ids:
            raise ValueError("Observed values require source evidence IDs")
        if self.classification == ValueClassification.ASSUMED and not self.assumption:
            raise ValueError("Assumed values require an explicit assumption")
        if self.classification != ValueClassification.ASSUMED and self.assumption is not None:
            raise ValueError("Only assumed values may carry an assumption")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "classification": self.classification.value,
            "source_evidence_ids": list(self.source_evidence_ids),
            "assumption": self.assumption,
        }


@dataclass(frozen=True)
class CapitalStructureScenario:
    """Analytical scenario, never a financing offer or recommendation."""

    scenario_id: str
    label: str
    financing_type: AnalyticalValue
    loan_to_value: AnalyticalValue
    loan_to_cost: AnalyticalValue
    property_value: AnalyticalValue
    total_project_cost: AnalyticalValue
    loan_amount: AnalyticalValue
    required_equity: AnalyticalValue
    interest_rate: AnalyticalValue
    term: AnalyticalValue
    amortization: AnalyticalValue
    refinancing_assumption: AnalyticalValue
    maturity: AnalyticalValue
    unknowns: Tuple[str, ...] = field(default_factory=tuple)
    sensitivity_parameters: Tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "unknowns", tuple(self.unknowns))
        object.__setattr__(self, "sensitivity_parameters", tuple(self.sensitivity_parameters))

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        for key in (
            "financing_type", "loan_to_value", "loan_to_cost", "property_value",
            "total_project_cost", "loan_amount", "required_equity", "interest_rate",
            "term", "amortization", "refinancing_assumption", "maturity",
        ):
            result[key] = getattr(self, key).to_dict()
        return result


def _validated_financing_evidence(evidence: Mapping[str, Any]) -> bool:
    validation = evidence.get("evidence_validation") or {}
    provenance = evidence.get("provenance") or {}
    return bool(
        evidence.get("evidence_id")
        and validation.get("decision_usable") is True
        and provenance.get("validation_status") == "VALIDATED"
    )


def _observed(value: Any, evidence_ids: Iterable[str]) -> AnalyticalValue:
    return AnalyticalValue(
        value=value,
        classification=ValueClassification.OBSERVED,
        source_evidence_ids=tuple(evidence_ids),
    )


def _unknown(name: str) -> AnalyticalValue:
    return AnalyticalValue(value=None, classification=ValueClassification.UNKNOWN), name


def _derived(value: Any, evidence_ids: Iterable[str]) -> AnalyticalValue:
    return AnalyticalValue(
        value=value,
        classification=ValueClassification.DERIVED,
        source_evidence_ids=tuple(evidence_ids),
    )


def _assumed(value: Any, assumption: str) -> AnalyticalValue:
    return AnalyticalValue(
        value=value,
        classification=ValueClassification.ASSUMED,
        assumption=assumption,
    )


def build_capital_structure_scenario(
    scenario_id: str,
    label: str,
    financing_evidence: Mapping[str, Any],
    *,
    property_value: float | None = None,
    total_project_cost: float | None = None,
    assumptions: Mapping[str, Any] | None = None,
) -> CapitalStructureScenario:
    """Build a deterministic analytical scenario from validated evidence.

    Only values actually present in validated evidence are classified as
    observed. Explicit caller-supplied values are classified as assumptions
    unless they are derived from supplied evidence. No missing financing term
    is inferred.
    """
    if not _validated_financing_evidence(financing_evidence):
        raise ValueError("Capital structure analysis requires explicitly validated financing evidence")

    evidence_id = str(financing_evidence["evidence_id"])
    claim = financing_evidence.get("claim") or {}
    assumptions = dict(assumptions or {})

    ltv = claim.get("loan_to_value")
    ltc = claim.get("loan_to_cost")
    loan_amount = None
    loan_amount_classification = ValueClassification.UNKNOWN
    loan_amount_sources: Tuple[str, ...] = ()
    unknowns = []

    if property_value is not None:
        property_value_value = _assumed(property_value, "property_value supplied for analytical scenario")
    else:
        property_value_value, missing = _unknown("property_value")
        unknowns.append(missing)

    if total_project_cost is not None:
        project_cost_value = _assumed(total_project_cost, "total_project_cost supplied for analytical scenario")
    else:
        project_cost_value, missing = _unknown("total_project_cost")
        unknowns.append(missing)

    if ltv is not None and property_value is not None:
        loan_amount = property_value * float(ltv) / 100.0
        loan_amount_classification = ValueClassification.DERIVED
        loan_amount_sources = (evidence_id,)
    else:
        unknowns.append("loan_amount")

    loan_amount_value = (
        _derived(loan_amount, loan_amount_sources)
        if loan_amount_classification == ValueClassification.DERIVED
        else _unknown("loan_amount")[0]
    )

    if loan_amount is not None and total_project_cost is not None:
        required_equity = total_project_cost - loan_amount
        required_equity_value = _derived(required_equity, (evidence_id,))
    else:
        required_equity_value, missing = _unknown("required_equity")
        unknowns.append(missing)

    if loan_amount is not None and total_project_cost:
        derived_ltc = loan_amount / total_project_cost * 100.0
        loan_to_cost_value = _derived(derived_ltc, (evidence_id,))
    elif ltc is not None:
        loan_to_cost_value = _observed(ltc, (evidence_id,))
    else:
        loan_to_cost_value, missing = _unknown("loan_to_cost")
        unknowns.append(missing)

    def observed_or_unknown(name: str) -> AnalyticalValue:
        value = claim.get(name)
        if value is not None:
            return _observed(value, (evidence_id,))
        unknowns.append(name)
        return _unknown(name)[0]

    interest_rate = observed_or_unknown("interest_rate")
    term = observed_or_unknown("term")
    amortization = observed_or_unknown("amortization")
    financing_type = observed_or_unknown("financing_type")

    refinancing = (
        _assumed(assumptions["refinancing_assumption"], "explicit analytical refinancing assumption")
        if "refinancing_assumption" in assumptions
        else _unknown("refinancing_assumption")[0]
    )
    if refinancing.classification == ValueClassification.UNKNOWN:
        unknowns.append("refinancing_assumption")

    maturity = (
        _assumed(assumptions["maturity"], "explicit analytical maturity assumption")
        if "maturity" in assumptions
        else _unknown("maturity")[0]
    )
    if maturity.classification == ValueClassification.UNKNOWN:
        unknowns.append("maturity")

    if ltv is None:
        ltv_value, missing = _unknown("loan_to_value")
        unknowns.append(missing)
    else:
        ltv_value = _observed(ltv, (evidence_id,))

    sensitivity_parameters = tuple(assumptions.get("sensitivity_parameters", ()))

    return CapitalStructureScenario(
        scenario_id=scenario_id,
        label=label,
        financing_type=financing_type,
        loan_to_value=ltv_value,
        loan_to_cost=loan_to_cost_value,
        property_value=property_value_value,
        total_project_cost=project_cost_value,
        loan_amount=loan_amount_value,
        required_equity=required_equity_value,
        interest_rate=interest_rate,
        term=term,
        amortization=amortization,
        refinancing_assumption=refinancing,
        maturity=maturity,
        unknowns=tuple(dict.fromkeys(unknowns)),
        sensitivity_parameters=sensitivity_parameters,
    )


def compare_capital_structures(
    scenarios: Iterable[CapitalStructureScenario],
) -> Dict[str, Any]:
    """Compare analytical consequences without ranking or selecting a structure."""
    items = tuple(scenarios)
    comparisons = []
    for index, left in enumerate(items):
        for right in items[index + 1 :]:
            comparisons.append({
                "left": left.scenario_id,
                "right": right.scenario_id,
                "differences": {
                    "loan_amount": _difference(left.loan_amount, right.loan_amount),
                    "required_equity": _difference(left.required_equity, right.required_equity),
                    "loan_to_value": _difference(left.loan_to_value, right.loan_to_value),
                    "loan_to_cost": _difference(left.loan_to_cost, right.loan_to_cost),
                },
            })
    return {
        "scenarios": [scenario.to_dict() for scenario in items],
        "pairwise_comparisons": comparisons,
        "ranking": None,
        "selected_scenario": None,
        "recommendation": None,
        "research_only": True,
        "investment_authority": False,
        "financing_authority": False,
        "execution_capability": False,
    }


def _difference(left: AnalyticalValue, right: AnalyticalValue) -> Dict[str, Any]:
    if left.value is None or right.value is None:
        return {"value": None, "status": "UNKNOWN"}
    try:
        return {"value": float(left.value) - float(right.value), "status": "DERIVED"}
    except (TypeError, ValueError):
        return {"value": None, "status": "NOT_NUMERIC"}
