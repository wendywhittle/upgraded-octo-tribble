"""Integration boundary for capital-structure analysis.

Capital-structure analysis is analytical context only. This adapter preserves
its provenance and epistemic classifications while making the existing
institutional pipeline able to consume it without creating a parallel
reasoning, risk, or authorization system.
"""

from typing import Any, Dict, Iterable


def build_capital_structure_context(
    scenarios: Iterable[Dict[str, Any]],
    *,
    pairwise_comparisons: Iterable[Dict[str, Any]] = (),
) -> Dict[str, Any]:
    """Build a read-only downstream context from existing analytical scenarios.

    The context is accepted only when every observed value retains an evidence
    ID. It carries no recommendation, ranking, selection, or authority field
    with an affirmative value.
    """
    scenario_list = [dict(item) for item in scenarios]
    evidence_ids = set()
    for scenario in scenario_list:
        for field_name, value in scenario.items():
            if isinstance(value, dict):
                classification = value.get("classification")
                ids = value.get("source_evidence_ids") or []
                if classification == "observed" and not ids:
                    raise ValueError(f"Observed capital-structure value {field_name!r} lacks evidence provenance")
                evidence_ids.update(str(item) for item in ids if item)

    return {
        "scenarios": scenario_list,
        "pairwise_comparisons": [dict(item) for item in pairwise_comparisons],
        "source_evidence_ids": sorted(evidence_ids),
        "epistemic_classes": ["observed", "derived", "assumed", "unknown"],
        "analytical_only": True,
        "recommendation": None,
        "ranking": None,
        "selected_scenario": None,
        "financing_authority": False,
        "investment_authority": False,
        "execution_capability": False,
        "brokerage_connectivity": False,
        "portfolio_mutation": False,
    }


def merge_research_context(
    research_context: Dict[str, Any] | None,
    capital_structure_context: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Attach capital-structure context without replacing existing research context."""
    merged = dict(research_context or {})
    if capital_structure_context is not None:
        merged["capital_structure"] = dict(capital_structure_context)
    return merged
