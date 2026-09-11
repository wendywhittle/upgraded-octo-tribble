"""Deterministic orchestration for assembling a complete investment case.

Phase 9 connects existing analytical components. It does not introduce a new
underwriting, scenario, simulation, financing, or decision engine.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.capital_stack import CapitalStack, FinancingAnalysis, analyze_capital_stack
from app.contrarian import ContrarianResult, review_contrarian
from app.cre_simulation import CRESimulationConfig, CRESimulationResult, run_cre_simulation
from app.investment_synthesis import InvestmentCaseSynthesis, synthesize_investment_case
from app.lender_intelligence import FinancingTerms, LenderProfile
from app.proforma import ProFormaInput, ProFormaResult, calculate_proforma
from app.scenario import ScenarioDefinition, ScenarioResult, ScenarioSet, run_scenario_set, standard_scenarios
from app.workflow import InvestmentCase


AssemblyStatus = Literal["INVESTMENT_CASE", "CONDITIONAL", "INSUFFICIENT_DATA"]
RecommendationStatus = Literal["PROCEED_TO_HUMAN_REVIEW", "CONDITIONAL_REVIEW", "NO_GO_RECOMMENDATION"]
OutputType = Literal["INTERPRETATION", "RECOMMENDATION"]


class InvestmentCaseAssemblyValidationError(ValueError):
    """Raised when assembly inputs cross an existing analytical boundary."""


class InvestmentCaseAssembly(BaseModel):
    """One auditable envelope containing outputs from existing engines."""

    model_config = ConfigDict(extra="forbid")

    case_identity: str
    assembly_version: str = "1"
    proforma: ProFormaResult
    scenarios: list[ScenarioResult] = Field(default_factory=list)
    simulations: list[CRESimulationResult] = Field(default_factory=list)
    financing: FinancingAnalysis | None = None
    lender_profiles: list[LenderProfile] = Field(default_factory=list)
    lender_terms: list[FinancingTerms] = Field(default_factory=list)
    contrarian: ContrarianResult | None = None
    synthesis: InvestmentCaseSynthesis
    status: AssemblyStatus
    recommendation: RecommendationStatus
    recommendation_rationale: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    output_types: dict[str, str] = Field(default_factory=lambda: {
        "status": "INTERPRETATION",
        "recommendation": "RECOMMENDATION",
        "recommendation_rationale": "INTERPRETATION",
    })


def _as_dicts(values: Iterable[BaseModel | dict[str, Any]]) -> list[dict[str, Any]]:
    return [deepcopy(v.model_dump(mode="json") if isinstance(v, BaseModel) else v) for v in values]


def _recommendation(
    synthesis: InvestmentCaseSynthesis,
    *,
    financing: FinancingAnalysis | None,
    lender_terms: list[FinancingTerms],
) -> tuple[AssemblyStatus, RecommendationStatus, list[str]]:
    reasons: list[str] = []
    if synthesis.thesis_status == "UNDETERMINED":
        reasons.append("The available analytical evidence does not establish an investment thesis.")
    if synthesis.thesis_status in {"CONDITIONAL", "FRAGILE"}:
        reasons.append(f"Synthesis classifies the thesis as {synthesis.thesis_status}.")
    if synthesis.unresolved_questions:
        reasons.append(f"{len(synthesis.unresolved_questions)} unresolved issue(s) remain visible.")
    if financing is None:
        reasons.append("No financing analysis was supplied; capital structure consequences remain unestablished.")
    if financing is not None and not financing.balanced:
        reasons.append("Capital sources and uses are not balanced.")
    if financing is not None and financing.total_debt > 0 and financing.debt_service_coverage_ratio is None:
        reasons.append("Debt service coverage could not be established from the supplied financing structure.")
    if lender_terms and any(t.evidence_status in {"INCOMPLETE", "CONTRADICTORY", "CONDITIONAL"} for t in lender_terms):
        reasons.append("Lender evidence contains conditional, incomplete, or contradictory observations.")
    if any("insufficient" in r.lower() or "cannot" in r.lower() for r in reasons):
        return "INSUFFICIENT_DATA", "NO_GO_RECOMMENDATION", reasons
    if synthesis.thesis_status in {"CONDITIONAL", "FRAGILE"} or reasons:
        return "CONDITIONAL", "CONDITIONAL_REVIEW", reasons
    return "INVESTMENT_CASE", "PROCEED_TO_HUMAN_REVIEW", [
        "Existing analytical outputs assembled without replacing human investment authority."
    ]


def assemble_investment_case(
    *,
    case_identity: str,
    proforma_input: ProFormaInput,
    scenarios: ScenarioSet | None = None,
    simulation_config: CRESimulationConfig | None = None,
    capital_stack: CapitalStack | None = None,
    lender_profiles: Iterable[LenderProfile] = (),
    lender_terms: Iterable[FinancingTerms] = (),
    evidence: Iterable[dict[str, Any]] = (),
    agent_perspectives: Iterable[dict[str, Any]] = (),
    disagreements: Iterable[dict[str, Any]] = (),
    investment_thesis: dict[str, Any] | None = None,
    scenario_input_version: str = "1",
) -> InvestmentCaseAssembly:
    """Assemble a complete case by connecting existing deterministic engines."""
    if not case_identity.strip():
        raise InvestmentCaseAssemblyValidationError("case_identity is required")
    if proforma_input.asset_id != case_identity:
        raise InvestmentCaseAssemblyValidationError("case_identity must match ProFormaInput.asset_id")

    profiles = [p for p in lender_profiles]
    terms = [t for t in lender_terms]
    proforma = calculate_proforma(proforma_input)

    scenario_set = scenarios or standard_scenarios()
    scenario_results = run_scenario_set(proforma_input, scenario_set, base_input_version=scenario_input_version).results
    simulation_results = [
        run_cre_simulation(
            proforma_input,
            result.scenario,
            config=simulation_config,
            base_input_version=scenario_input_version,
        )
        for result in scenario_results
    ]

    financing = analyze_capital_stack(capital_stack, proforma=proforma) if capital_stack is not None else None

    evidence_payload = _as_dicts(evidence)
    lender_evidence = evidence_payload + [
        {
            "evidence_id": f"lender:{term.financing_id}",
            "claim": f"Lender financing terms observed for {term.lender_id}",
            "status": term.evidence_status,
            "provenance": _as_dicts(term.provenance),
            "conflict_status": term.conflict_status,
            "conflicting_financing_ids": list(term.conflicting_financing_ids),
        }
        for term in terms
    ]

    contrarian = review_contrarian(
        case_identity=case_identity,
        proforma=proforma,
        scenarios=scenario_results,
        simulations=simulation_results,
        evidence=lender_evidence,
        agent_perspectives=agent_perspectives,
    )
    synthesis = synthesize_investment_case(
        case_identity=case_identity,
        proforma=proforma,
        scenarios=scenario_results,
        simulations=simulation_results,
        contrarian=contrarian,
        evidence=lender_evidence,
        agent_perspectives=agent_perspectives,
        disagreements=disagreements,
        investment_thesis=investment_thesis,
    )
    status, recommendation, rationale = _recommendation(
        synthesis,
        financing=financing,
        lender_terms=terms,
    )

    return InvestmentCaseAssembly(
        case_identity=case_identity,
        proforma=proforma,
        scenarios=scenario_results,
        simulations=simulation_results,
        financing=financing,
        lender_profiles=profiles,
        lender_terms=terms,
        contrarian=contrarian,
        synthesis=synthesis,
        status=status,
        recommendation=recommendation,
        recommendation_rationale=rationale,
        provenance={
            "flow": [
                "DEAL",
                "PRO_FORMA",
                "SCENARIOS",
                "SIMULATION",
                "CONTRARIAN",
                "CAPITAL_STACK",
                "LENDER_EVIDENCE",
                "INVESTMENT_SYNTHESIS",
            ],
            "calculations": "AUTHORITATIVE_IN_ORIGINATING_ENGINES",
            "synthesis": "INTERPRETATION",
            "recommendation": "RECOMMENDATION",
            "human_authority": "EXPLICIT_AND_SEPARATE",
        },
    )


def apply_assembly_to_case(case: InvestmentCase, assembly: InvestmentCaseAssembly) -> InvestmentCase:
    """Return a copied InvestmentCase envelope without workflow mutation."""
    if case.deal_id != assembly.case_identity:
        raise InvestmentCaseAssemblyValidationError("InvestmentCase deal_id does not match assembly case_identity")
    return case.model_copy(update={
        "evidence": _as_dicts(assembly.synthesis.thesis.supporting_evidence),
        "proforma": assembly.proforma.model_dump(mode="json"),
        "scenarios": {"results": _as_dicts(assembly.scenarios)},
        "simulation_results": {"results": _as_dicts(assembly.simulations)},
        "financing": assembly.financing.model_dump(mode="json") if assembly.financing else None,
        "capital_stack": None,
        "contrarian_findings": _as_dicts(assembly.contrarian.findings) if assembly.contrarian else [],
        "margin_of_safety": assembly.contrarian.margin_of_safety.model_dump(mode="json") if assembly.contrarian else None,
        "investment_thesis": assembly.synthesis.thesis.model_dump(mode="json"),
        "disagreement": _as_dicts(assembly.synthesis.disagreements),
        "audit_metadata": {
            **deepcopy(case.audit_metadata),
            "investment_case_assembly": assembly.model_dump(mode="json"),
        },
    })
