"""Deterministic adversarial review for CRE underwriting.

The Contrarian interprets existing calculation and evidence outputs. It does not
recalculate financial or stochastic metrics and cannot mutate workflow state.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.cre_simulation import CRESimulationResult
from app.proforma import ProFormaResult
from app.scenario import ScenarioResult


class ContrarianValidationError(ValueError):
    """Raised when an adversarial review cannot be performed safely."""


FindingCategory = Literal[
    "REVENUE", "OCCUPANCY", "EXPENSE", "VALUATION", "EXIT", "LIQUIDITY",
    "FINANCING", "EVIDENCE", "MODEL", "ASSUMPTION", "CONCENTRATION",
    "OPERATIONS", "OTHER",
]
FindingSeverity = Literal["LOW", "MODERATE", "MATERIAL", "CRITICAL"]
FindingStatus = Literal["OPEN", "UNRESOLVED", "INSUFFICIENT_DATA", "NOTED"]
OutputType = Literal["OBSERVATION", "INTERPRETATION", "RECOMMENDATION"]
MarginStatus = Literal["SUFFICIENT", "THIN", "INSUFFICIENT", "UNDETERMINED"]


class ContrarianFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: FindingCategory
    severity: FindingSeverity
    description: str
    affected_assumption: str | None = None
    affected_scenario: str | None = None
    supporting_evidence: list[Dict[str, Any]] = Field(default_factory=list)
    supporting_simulation_output: Dict[str, Any] = Field(default_factory=dict)
    rationale: str
    provenance: Literal[
        "FACT", "SOURCE", "ASSUMPTION", "HYPOTHESIS", "CALCULATION",
        "INTERPRETATION", "PREDICTION", "RECOMMENDATION",
    ]
    status: FindingStatus = "OPEN"
    output_type: OutputType = "INTERPRETATION"


class MarginOfSafetyAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: MarginStatus
    components: Dict[str, Any] = Field(default_factory=dict)
    rationale: list[str] = Field(default_factory=list)
    provenance: Literal["INTERPRETATION"] = "INTERPRETATION"


class ContrarianResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_identity: str
    scenarios_reviewed: list[str]
    simulations_reviewed: list[str]
    findings: list[ContrarianFinding]
    margin_of_safety: MarginOfSafetyAssessment
    unresolved_questions: list[str] = Field(default_factory=list)
    recommended_diligence: list[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    output_type: Literal["INTERPRETATION", "RECOMMENDATION"] = "INTERPRETATION"


_CALCULATION_FIELDS = {
    "irr", "unlevered_irr", "noi", "valuation", "entry_valuation",
    "exit_valuation", "terminal_value", "equity_multiple",
    "unlevered_equity_multiple", "probability_loss", "drawdown",
    "max_drawdown_mean", "mean_terminal", "median_terminal",
    "p05_terminal", "p95_terminal",
}


def _reject_calculated_agent_claims(agent_perspectives: Iterable[Dict[str, Any]]) -> None:
    for perspective in agent_perspectives:
        for key in perspective:
            if key.lower() in _CALCULATION_FIELDS:
                raise ContrarianValidationError(
                    f"Agent perspective cannot supply authoritative calculated output: {key}"
                )


def _simulation_summary(result: CRESimulationResult) -> Dict[str, Any]:
    summary = result.simulation.get("summary", {})
    if not isinstance(summary, dict):
        raise ContrarianValidationError("Simulation summary is malformed")
    return dict(summary)


def _scenario_identity(result: ScenarioResult) -> str:
    return result.scenario.name


def _scenario_findings(results: list[ScenarioResult]) -> list[ContrarianFinding]:
    findings: list[ContrarianFinding] = []
    names = {result.scenario.name.upper() for result in results}
    for result in results:
        scenario = result.scenario.name.upper()
        overrides = result.scenario.overrides
        if "exit_cap_rate" in overrides:
            findings.append(ContrarianFinding(
                category="EXIT",
                severity="MODERATE" if scenario != "ADVERSARIAL" else "MATERIAL",
                description="Scenario explicitly changes the exit capitalization assumption.",
                affected_assumption="exit_cap_rate",
                affected_scenario=result.scenario.name,
                rationale="Exit valuation is produced by the Pro Forma using the scenario's validated exit-cap assumption.",
                provenance="HYPOTHESIS",
                status="NOTED",
            ))
        if "initial_occupancy" in overrides and float(overrides["initial_occupancy"]) < 0.90:
            findings.append(ContrarianFinding(
                category="OCCUPANCY",
                severity="MATERIAL",
                description="Scenario assumes occupancy below 90%.",
                affected_assumption="initial_occupancy",
                affected_scenario=result.scenario.name,
                rationale="The scenario explicitly introduces a material occupancy stress.",
                provenance="HYPOTHESIS",
            ))
        if "rent_growth" in overrides and float(overrides["rent_growth"]) <= 0:
            findings.append(ContrarianFinding(
                category="REVENUE",
                severity="MATERIAL",
                description="Scenario assumes no positive rent growth.",
                affected_assumption="rent_growth",
                affected_scenario=result.scenario.name,
                rationale="The scenario removes positive rent-growth support from the underwriting hypothesis.",
                provenance="HYPOTHESIS",
            ))
        if "expense_growth" in overrides and float(overrides["expense_growth"]) > 0.04:
            findings.append(ContrarianFinding(
                category="EXPENSE",
                severity="MATERIAL",
                description="Scenario assumes elevated expense growth.",
                affected_assumption="expense_growth",
                affected_scenario=result.scenario.name,
                rationale="The scenario explicitly stresses operating-cost growth.",
                provenance="HYPOTHESIS",
            ))
    if len(names) < 2:
        findings.append(ContrarianFinding(
            category="ASSUMPTION",
            severity="MODERATE",
            description="Only one deterministic scenario is available for adversarial comparison.",
            rationale="Scenario fragility cannot be assessed across cases without comparable scenarios.",
            provenance="INTERPRETATION",
            status="INSUFFICIENT_DATA",
        ))
    return findings


def _simulation_findings(simulations: list[CRESimulationResult]) -> list[ContrarianFinding]:
    findings: list[ContrarianFinding] = []
    for result in simulations:
        summary = _simulation_summary(result)
        regime = result.simulation_regime.upper()
        severity: FindingSeverity = "MATERIAL" if regime == "ADVERSARIAL" else "LOW"
        findings.append(ContrarianFinding(
            category="MODEL",
            severity=severity,
            description=f"Simulation distribution reviewed for {result.scenario.name} using the existing {regime} regime.",
            affected_scenario=result.scenario.name,
            supporting_simulation_output=summary,
            rationale="The probability, percentile, and drawdown values are consumed directly from the independent Monte Carlo engine.",
            provenance="CALCULATION",
            output_type="OBSERVATION",
            status="NOTED",
        ))
    return findings


def review_contrarian(
    *,
    case_identity: str,
    proforma: ProFormaResult | None = None,
    scenarios: Iterable[ScenarioResult] = (),
    simulations: Iterable[CRESimulationResult] = (),
    evidence: Iterable[Dict[str, Any]] = (),
    agent_perspectives: Iterable[Dict[str, Any]] = (),
) -> ContrarianResult:
    """Review existing underwriting outputs without recalculating them."""
    if not case_identity.strip():
        raise ContrarianValidationError("case_identity is required")
    _reject_calculated_agent_claims(agent_perspectives)

    scenario_list = list(scenarios)
    simulation_list = list(simulations)
    evidence_list = [dict(item) for item in evidence]

    if proforma is None and not scenario_list:
        raise ContrarianValidationError("ProFormaResult or ScenarioResult is required")
    if scenario_list and proforma is not None:
        if any(result.proforma.asset_id != proforma.asset_id for result in scenario_list):
            raise ContrarianValidationError("Scenario and Pro Forma asset identities do not match")
    if simulation_list and scenario_list:
        scenario_names = {result.scenario.name for result in scenario_list}
        if any(result.scenario.name not in scenario_names for result in simulation_list):
            raise ContrarianValidationError("Simulation references an unreviewed scenario")

    findings = _scenario_findings(scenario_list)
    findings.extend(_simulation_findings(simulation_list))

    if evidence_list:
        for item in evidence_list:
            if not item.get("evidence_id") or not item.get("claim"):
                findings.append(ContrarianFinding(
                    category="EVIDENCE", severity="MATERIAL",
                    description="Evidence item is missing required identity or claim information.",
                    supporting_evidence=[item],
                    rationale="Material claims without identifiable evidence cannot be safely relied upon.",
                    provenance="SOURCE", status="INSUFFICIENT_DATA",
                ))
    else:
        findings.append(ContrarianFinding(
            category="EVIDENCE", severity="MODERATE",
            description="No evidence records were supplied for adversarial review.",
            rationale="Evidence quality cannot be assessed without evidence inputs.",
            provenance="INTERPRETATION", status="INSUFFICIENT_DATA",
        ))

    unresolved = [
        "Which material underwriting assumptions have independent evidence?",
        "Which tenant, market, liquidity, and financing risks remain unsupported by supplied data?",
    ]
    diligence = [
        "Validate material assumptions against current, decision-usable evidence.",
        "Investigate any unresolved tenant, liquidity, financing, and operational risks before authorization.",
    ]
    if any(f.severity in {"MATERIAL", "CRITICAL"} for f in findings):
        margin_status: MarginStatus = "THIN"
        margin_rationale = ["Material adversarial findings require additional review before relying on the underwriting thesis."]
    else:
        margin_status = "UNDETERMINED"
        margin_rationale = ["The available structured inputs do not establish a sufficient margin-of-safety conclusion."]

    if any(f.category == "EVIDENCE" and f.status == "INSUFFICIENT_DATA" for f in findings):
        margin_status = "UNDETERMINED"
        margin_rationale = ["Evidence sufficiency is unresolved; margin of safety cannot be established from supplied inputs."]

    return ContrarianResult(
        case_identity=case_identity,
        scenarios_reviewed=[_scenario_identity(result) for result in scenario_list],
        simulations_reviewed=[f"{result.scenario.name}:{result.simulation_config.seed}" for result in simulation_list],
        findings=findings,
        margin_of_safety=MarginOfSafetyAssessment(
            status=margin_status,
            components={
                "valuation_cushion": "NOT_ASSESSED",
                "downside_return_deterioration": "OBSERVED_FROM_SCENARIO_RESULTS",
                "probability_of_loss": "OBSERVED_FROM_SIMULATION_RESULTS",
                "downside_percentile": "OBSERVED_FROM_SIMULATION_RESULTS",
                "drawdown": "OBSERVED_FROM_SIMULATION_RESULTS",
                "terminal_value_dependence": "NOT_RECALCULATED",
                "assumption_sensitivity": "OBSERVED_FROM_SCENARIO_OVERRIDES",
                "evidence_strength": "REQUIRES_EVIDENCE_INPUTS",
                "unresolved_risks": len(unresolved),
            },
            rationale=margin_rationale,
        ),
        unresolved_questions=unresolved,
        recommended_diligence=diligence,
        provenance={"source_layers": ["PRO_FORMA", "SCENARIO", "SIMULATION", "EVIDENCE"]},
    )
