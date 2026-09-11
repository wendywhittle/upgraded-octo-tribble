"""Shared domain vocabulary for AletheiaTelos investment intelligence.

This module defines the boundary between the Capital Engine and Asset Engine without
creating execution authority. Both domains consume the same evidence and reasoning
infrastructure downstream.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


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


@dataclass(frozen=True)
class CrossAssetLink:
    """A typed relationship that can connect capital and real-asset research."""

    from_entity: IntelligenceEntity
    relationship: str
    to_entity: IntelligenceEntity
    evidence_ids: List[str] = field(default_factory=list)


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
