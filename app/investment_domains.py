"""Shared domain vocabulary for AletheiaTelos investment intelligence.

This module defines the boundary between the Capital Engine and Asset Engine without
creating execution authority. Both domains consume the same evidence and reasoning
infrastructure downstream.
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional


class InvestmentDomain(str, Enum):
    CAPITAL = "capital"
    ASSET = "asset"


class EvidenceStage(str, Enum):
    OBSERVATION = "observation"
    EVIDENCE = "evidence"
    INTERPRETATION = "interpretation"
    HYPOTHESIS = "hypothesis"
    SCENARIO_ASSUMPTION = "scenario_assumption"


class CapitalResearchDomain(str, Enum):
    PUBLIC_MARKETS = "public_markets"
    QUANTITATIVE = "quantitative"
    ALTERNATIVE_DATA = "alternative_data"
    MACRO = "macro"
    FACTORS = "factors"
    MARKET_REGIMES = "market_regimes"
    RISK = "risk"
    PORTFOLIO = "portfolio"


class AssetResearchDomain(str, Enum):
    CRE = "cre"
    INDUSTRIAL = "industrial"
    NNN = "nnn"
    INFRASTRUCTURE = "infrastructure"
    DEVELOPMENT = "development"
    PRIVATE_ASSETS = "private_assets"
    OPERATIONS = "operations"
    CAPITAL_STRUCTURE = "capital_structure"


@dataclass(frozen=True)
class IntelligenceEntity:
    """A lightweight cross-asset entity reference, not a graph database."""

    entity_id: str
    entity_type: str
    name: str
    geography: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ResearchHypothesis:
    """A testable interpretation derived from evidence, never an observation."""

    hypothesis_id: str
    statement: str
    domain: InvestmentDomain
    research_domains: List[str]
    evidence_ids: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    invalidation_conditions: List[str] = field(default_factory=list)
    research_questions: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class CrossAssetLink:
    """A typed relationship connecting capital and real-asset research."""

    from_entity: IntelligenceEntity
    relationship: str
    to_entity: IntelligenceEntity
    evidence_ids: List[str] = field(default_factory=list)


def classify_cross_asset_links(
    links: Iterable[CrossAssetLink], evidence_ids: Iterable[str]
) -> List[Dict[str, Any]]:
    """Serialize links while explicitly separating backed relationships from hypotheses.

    A link is ``evidence_backed`` only when every referenced evidence ID exists in the
    evidence registry for the current research request. Unbacked links remain useful
    context, but are never silently promoted to observations or evidence.
    """
    available = {str(item) for item in evidence_ids}
    classified: List[Dict[str, Any]] = []
    for link in links:
        missing = sorted(set(link.evidence_ids) - available)
        item = asdict(link)
        item["evidence_backed"] = bool(link.evidence_ids) and not missing
        item["missing_evidence_ids"] = missing
        item["epistemic_stage"] = (
            EvidenceStage.EVIDENCE.value
            if item["evidence_backed"]
            else EvidenceStage.HYPOTHESIS.value
        )
        classified.append(item)
    return classified


def cross_asset_hypotheses(
    links: Iterable[CrossAssetLink], evidence_ids: Iterable[str]
) -> List[ResearchHypothesis]:
    """Turn cross-asset context into explicit, testable hypotheses.

    This function never asserts that a relationship is true. Each generated
    hypothesis points back to the relationship's supplied evidence IDs, if any,
    so downstream agents can test the link rather than inherit it as fact.
    """
    available = {str(item) for item in evidence_ids}
    hypotheses: List[ResearchHypothesis] = []
    for index, link in enumerate(links, start=1):
        valid_evidence_ids = [item for item in link.evidence_ids if item in available]
        geography = f" in {link.to_entity.geography}" if link.to_entity.geography else ""
        relationship = link.relationship.replace("_", " ")
        statement = f"{link.from_entity.name} may {relationship} {link.to_entity.name}{geography}."
        research_question = (
            f"What independent evidence would confirm or falsify whether "
            f"{link.from_entity.name} {relationship} {link.to_entity.name}{geography}?"
        )
        hypotheses.append(
            ResearchHypothesis(
                hypothesis_id=f"cross-asset-{index}",
                statement=statement,
                domain=InvestmentDomain.ASSET,
                research_domains=[AssetResearchDomain.CRE.value],
                evidence_ids=valid_evidence_ids,
                assumptions=["The stated cross-asset relationship is testable and may be false."],
                invalidation_conditions=["Available evidence fails to support the stated relationship."],
                research_questions=[research_question],
            )
        )
    return hypotheses


def domain_manifest() -> Dict[str, Any]:
    """Return the stable public manifest of the two investment engines."""
    return {
        "capital_engine": [item.value for item in CapitalResearchDomain],
        "asset_engine": [item.value for item in AssetResearchDomain],
        "shared_layers": [
            "evidence_registry",
            "computational_kaleidoscope",
            "conflict_coexistence",
            "independent_simulation",
            "contrarian_review",
            "human_investment_committee",
            "outcome_attribution",
            "epistemic_memory",
        ],
        "execution_authority": False,
    }
