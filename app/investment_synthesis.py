"""Deterministic Investment Case synthesis.

This module extends the existing Meta-Intelligence process evaluator with a
structured synthesis boundary. It consumes authoritative outputs from existing
engines and never mutates workflow, authorization, portfolio, or calculations.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.contrarian import ContrarianResult
from app.cre_simulation import CRESimulationResult
from app.proforma import ProFormaResult
from app.scenario import ScenarioResult
from app.workflow import InvestmentCase

ThesisStatus = Literal["SUPPORTED", "CONDITIONAL", "FRAGILE", "UNSUPPORTED", "UNDETERMINED"]
AgreementStatus = Literal["AGREEMENT", "MINOR_DISAGREEMENT", "MATERIAL_DISAGREEMENT", "UNRESOLVED", "INSUFFICIENT_DATA"]
OutputType = Literal["INTERPRETATION", "RECOMMENDATION"]


class SynthesisValidationError(ValueError):
    """Raised when synthesis inputs cross an analytical boundary."""


class SynthesisDisagreement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topic: str
    status: AgreementStatus
    perspectives: list[str] = Field(default_factory=list)
    positions: list[str] = Field(default_factory=list)
    supporting_evidence: list[Dict[str, Any]] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    provenance: Literal["INTERPRETATION"] = "INTERPRETATION"


class InvestmentThesis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    opportunity: str
    economic_rationale: list[str] = Field(default_factory=list)
    supporting_evidence: list[Dict[str, Any]] = Field(default_factory=list)
    key_assumptions: list[str] = Field(default_factory=list)
    scenario_resilience: list[str] = Field(default_factory=list)
    principal_risks: list[str] = Field(default_factory=list)
    contrarian_objections: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    required_diligence: list[str] = Field(default_factory=list)
    thesis_dependencies: list[str] = Field(default_factory=list)


class InvestmentCaseSynthesis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_identity: str
    perspectives_reviewed: list[str] = Field(default_factory=list)
    evidence_reviewed: list[str] = Field(default_factory=list)
    scenarios_reviewed: list[str] = Field(default_factory=list)
    simulations_reviewed: list[str] = Field(default_factory=list)
    contrarian_reviewed: bool = False
    agreements: list[str] = Field(default_factory=list)
    disagreements: list[SynthesisDisagreement] = Field(default_factory=list)
    dominant_risks: list[str] = Field(default_factory=list)
    thesis: InvestmentThesis
    thesis_status: ThesisStatus
    key_assumptions: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    recommended_diligence: list[str] = Field(default_factory=list)
    synthesis: str
    provenance: Dict[str, Any] = Field(default_factory=dict)
    output_type: OutputType = "INTERPRETATION"


_CALCULATION_KEYS = {"irr", "unlevered_irr", "noi", "valuation", "entry_valuation", "exit_valuation", "terminal_value", "equity_multiple", "unlevered_equity_multiple", "probability_loss", "drawdown", "max_drawdown_mean", "mean_terminal", "median_terminal", "p05_terminal", "p95_terminal"}
_VALID_DISAGREEMENT = {"AGREEMENT", "MINOR_DISAGREEMENT", "MATERIAL_DISAGREEMENT", "UNRESOLVED", "INSUFFICIENT_DATA"}


def _unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(str(v) for v in values if v))


def _reject_agent_calculations(perspectives: Iterable[Dict[str, Any]]) -> None:
    for perspective in perspectives:
        for key in perspective:
            if key.lower() in _CALCULATION_KEYS:
                raise SynthesisValidationError(f"Agent perspective cannot supply authoritative calculated output: {key}")


def _scenario_review(scenarios: list[ScenarioResult]) -> tuple[list[str], list[str]]:
    by_name = {r.scenario.name.upper(): r for r in scenarios}
    observations: list[str] = []
    risks: list[str] = []
    base = by_name.get("BASE")
    if not base:
        return observations, risks
    for name in ("DOWNSIDE", "ADVERSARIAL", "UPSIDE"):
        current = by_name.get(name)
        if not current:
            continue
        base_irr, current_irr = base.proforma.unlevered_irr, current.proforma.unlevered_irr
        if base_irr is not None and current_irr is not None:
            delta = current_irr - base_irr
            observations.append(f"{name} unlevered IRR changes by {delta:.6f} versus BASE; value consumed from Pro Forma output.")
            if name in {"DOWNSIDE", "ADVERSARIAL"} and delta < 0:
                risks.append(f"{name} deteriorates return relative to BASE.")
        if current.proforma.annual[-1].noi < base.proforma.annual[-1].noi:
            observations.append(f"{name} terminal-year NOI is below BASE; no new NOI calculation was performed.")
    return observations, risks


def _simulation_review(simulations: list[CRESimulationResult]) -> tuple[list[str], list[str]]:
    by_name = {r.scenario.name.upper(): r.simulation.get("summary", {}) for r in simulations}
    observations: list[str] = []
    risks: list[str] = []
    base = by_name.get("BASE")
    for name in ("DOWNSIDE", "ADVERSARIAL", "UPSIDE"):
        current = by_name.get(name)
        if not current:
            continue
        p_loss, base_loss = current.get("probability_loss"), base.get("probability_loss") if base else None
        if isinstance(p_loss, (int, float)) and isinstance(base_loss, (int, float)):
            observations.append(f"{name} probability_loss is {p_loss:.4f} versus BASE {base_loss:.4f}; consumed from Monte Carlo output.")
            if name in {"DOWNSIDE", "ADVERSARIAL"} and p_loss > base_loss:
                risks.append(f"{name} has higher simulated loss probability than BASE.")
        dd = current.get("max_drawdown_mean")
        if isinstance(dd, (int, float)) and dd > 0.20:
            risks.append(f"{name} reports mean maximum drawdown above 20%.")
    return observations, risks


def _evidence_review(evidence: list[Dict[str, Any]]) -> tuple[list[str], list[str], list[str]]:
    reviewed, unresolved, risks = [], [], []
    claims: dict[str, list[Dict[str, Any]]] = {}
    for item in evidence:
        if item.get("evidence_id"): reviewed.append(str(item["evidence_id"]))
        claim = item.get("claim")
        if not claim:
            unresolved.append("Evidence item without an identifiable claim.")
            continue
        key = str(claim).strip().lower(); claims.setdefault(key, []).append(item)
        status = str(item.get("status", "")).upper()
        if status in {"UNRESOLVED", "INSUFFICIENT_DATA", "CONTRADICTORY"}:
            unresolved.append(f"Evidence claim remains {status}: {claim}")
            risks.append(f"Evidence uncertainty remains around: {claim}")
    for claim, items in claims.items():
        if len(items) > 1 and any(item.get("contradictory") for item in items):
            unresolved.append(f"Contradictory evidence preserved for claim: {claim}")
    return reviewed, unresolved, risks


def synthesize_investment_case(*, case_identity: str, proforma: ProFormaResult | None = None,
                               scenarios: Iterable[ScenarioResult] = (), simulations: Iterable[CRESimulationResult] = (),
                               contrarian: ContrarianResult | None = None, evidence: Iterable[Dict[str, Any]] = (),
                               agent_perspectives: Iterable[Dict[str, Any]] = (), disagreements: Iterable[Dict[str, Any]] = (),
                               investment_thesis: Dict[str, Any] | None = None) -> InvestmentCaseSynthesis:
    """Synthesize validated outputs; financial calculations remain authoritative upstream."""
    if not case_identity.strip():
        raise SynthesisValidationError("case_identity is required")
    agents = [dict(x) for x in agent_perspectives]; _reject_agent_calculations(agents)
    scenario_list, simulation_list, evidence_list = list(scenarios), list(simulations), [dict(x) for x in evidence]
    if proforma is None and not scenario_list and not simulation_list and contrarian is None:
        raise SynthesisValidationError("At least one validated analytical output is required")
    if proforma and scenario_list and any(r.proforma.asset_id != proforma.asset_id for r in scenario_list):
        raise SynthesisValidationError("Scenario and Pro Forma asset identities do not match")
    if scenario_list and simulation_list:
        names = {r.scenario.name for r in scenario_list}
        if any(r.scenario.name not in names for r in simulation_list):
            raise SynthesisValidationError("Simulation references an unreviewed scenario")
    if contrarian and contrarian.case_identity != case_identity:
        raise SynthesisValidationError("Contrarian case identity does not match synthesis case")

    structured_disagreements: list[SynthesisDisagreement] = []
    for item in disagreements:
        data = dict(item); status = data.get("status", "UNRESOLVED")
        if status not in _VALID_DISAGREEMENT:
            raise SynthesisValidationError(f"Invalid disagreement status: {status}")
        structured_disagreements.append(SynthesisDisagreement(topic=str(data.get("topic") or data.get("proposition") or "Unspecified disagreement"), status=status, perspectives=list(data.get("perspectives", [])), positions=list(data.get("positions", [])), supporting_evidence=list(data.get("supporting_evidence", [])), unresolved_questions=list(data.get("unresolved_questions", []))))

    evidence_ids, evidence_unresolved, evidence_risks = _evidence_review(evidence_list)
    scenario_obs, scenario_risks = _scenario_review(scenario_list)
    simulation_obs, simulation_risks = _simulation_review(simulation_list)
    contrarian_risks, contrarian_questions, diligence = [], [], []
    if contrarian:
        for finding in contrarian.findings:
            if finding.severity in {"MATERIAL", "CRITICAL"}:
                contrarian_risks.append(finding.description)
        contrarian_questions.extend(contrarian.unresolved_questions); diligence.extend(contrarian.recommended_diligence)

    dominant_risks = _unique(scenario_risks + simulation_risks + evidence_risks + contrarian_risks)
    unresolved = _unique(evidence_unresolved + contrarian_questions + [q for d in structured_disagreements for q in d.unresolved_questions])
    assumptions = _unique([str(v) for p in agents for v in p.get("assumptions", []) if v])
    if proforma: assumptions.extend(["Pro Forma financial outputs are authoritative calculations from the existing engine.", "Underlying underwriting assumptions require evidence validation."])
    assumptions = _unique(assumptions)
    material_disagreement = any(d.status in {"MATERIAL_DISAGREEMENT", "UNRESOLVED", "INSUFFICIENT_DATA"} for d in structured_disagreements)
    if not evidence_list and not scenario_list and not simulation_list and not contrarian: status: ThesisStatus = "UNDETERMINED"
    elif unresolved or material_disagreement: status = "CONDITIONAL"
    elif dominant_risks: status = "FRAGILE"
    else: status = "SUPPORTED" if (proforma or scenario_list or simulation_list) else "UNDETERMINED"
    if contrarian and contrarian.margin_of_safety.status == "INSUFFICIENT": status = "FRAGILE"
    if contrarian and contrarian.margin_of_safety.status == "UNDETERMINED" and not evidence_list: status = "UNDETERMINED"

    original = investment_thesis or {}
    rationale = _unique(scenario_obs + simulation_obs)
    if not rationale and proforma: rationale = ["Deterministic Pro Forma outputs were reviewed without recalculation."]
    thesis = InvestmentThesis(opportunity=str(original.get("opportunity") or "Opportunity requires human review of the available investment case."), economic_rationale=rationale, supporting_evidence=evidence_list, key_assumptions=assumptions, scenario_resilience=scenario_obs, principal_risks=dominant_risks, contrarian_objections=contrarian_risks, unresolved_questions=unresolved, required_diligence=_unique(diligence), thesis_dependencies=["validated evidence", "underwriting assumptions"])
    synthesis = f"The investment case is analytically {status.lower()}. {len(agents)} perspective(s), {len(evidence_ids)} evidence record(s), {len(scenario_list)} scenario(s), and {len(simulation_list)} simulation result(s) were reviewed. {len(dominant_risks)} dominant risk(s) and {len(unresolved)} unresolved issue(s) remain. This synthesis is analytical and does not constitute authorization."
    return InvestmentCaseSynthesis(case_identity=case_identity, perspectives_reviewed=[str(p["agent_id"]) for p in agents if p.get("agent_id")], evidence_reviewed=evidence_ids, scenarios_reviewed=[r.scenario.name for r in scenario_list], simulations_reviewed=[f"{r.scenario.name}:{r.simulation_config.seed}" for r in simulation_list], contrarian_reviewed=contrarian is not None, agreements=["Validated calculation outputs remain authoritative in their originating engines."], disagreements=structured_disagreements, dominant_risks=dominant_risks, thesis=thesis, thesis_status=status, key_assumptions=assumptions, unresolved_questions=unresolved, recommended_diligence=_unique(diligence), synthesis=synthesis, provenance={"layers": ["EVIDENCE", "AGENT_REASONING", "PRO_FORMA", "SCENARIO", "SIMULATION", "CONTRARIAN"]}, output_type="INTERPRETATION")


def apply_synthesis_to_case(case: InvestmentCase, result: InvestmentCaseSynthesis) -> InvestmentCase:
    """Return a copied InvestmentCase envelope without changing workflow or authorization."""
    if case.deal_id != result.case_identity:
        raise SynthesisValidationError("InvestmentCase deal_id does not match synthesis case_identity")
    return case.model_copy(update={"investment_thesis": result.thesis.model_dump(mode="json"), "disagreement": [d.model_dump(mode="json") for d in result.disagreements]})
