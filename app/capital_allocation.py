"""Research-only capital allocation diagnostics.

This module evaluates explicitly supplied portfolio weights and constraints. It
never chooses trades, submits orders, mutates a portfolio, or invents missing
risk inputs.
"""

from typing import Any, Dict, List


def assess_allocation(positions: List[Dict[str, Any]], gross_exposure: float | None = None) -> Dict[str, Any]:
    """Return transparent allocation diagnostics from supplied position data."""
    if not positions:
        return {
            "status": "NO_DATA",
            "position_count": 0,
            "gross_exposure": gross_exposure,
            "concentration": None,
            "positions": [],
            "limit_breaches": [],
            "research_only": True,
            "investment_authority": False,
        }

    cleaned = []
    for position in positions:
        name = str(position.get("name", "")).strip()
        weight = position.get("weight")
        if not name:
            raise ValueError("Each position requires a name.")
        if weight is None:
            raise ValueError(f"Position '{name}' is missing weight; no weight is inferred.")
        weight = float(weight)
        if weight < 0 or weight > 1:
            raise ValueError(f"Position '{name}' weight must be between 0 and 1.")
        item = {"name": name, "weight": weight}
        if position.get("max_weight") is not None:
            max_weight = float(position["max_weight"])
            if max_weight < 0 or max_weight > 1:
                raise ValueError(f"Position '{name}' max_weight must be between 0 and 1.")
            item["max_weight"] = max_weight
        cleaned.append(item)

    total = sum(item["weight"] for item in cleaned)
    concentration = max(item["weight"] for item in cleaned)
    breaches = [
        {"name": item["name"], "weight": item["weight"], "max_weight": item["max_weight"]}
        for item in cleaned
        if "max_weight" in item and item["weight"] > item["max_weight"]
    ]
    return {
        "status": "REVIEW" if breaches or total > 1 else "WITHIN_SUPPLIED_LIMITS",
        "position_count": len(cleaned),
        "gross_exposure": gross_exposure,
        "weight_sum": total,
        "cash_or_unallocated_weight": max(0.0, 1.0 - total),
        "concentration": concentration,
        "positions": cleaned,
        "limit_breaches": breaches,
        "unknowns": ([] if gross_exposure is not None else ["gross_exposure"]),
        "research_only": True,
        "investment_authority": False,
    }


def capital_allocation_manifest() -> Dict[str, Any]:
    return {
        "subsystem": "capital_allocation_intelligence",
        "purpose": "portfolio exposure and constraint diagnostics",
        "inputs_required": ["positions[].name", "positions[].weight"],
        "optional_inputs": ["positions[].max_weight", "gross_exposure"],
        "does_not": ["select_trades", "submit_orders", "mutate_portfolios", "infer_missing_risk"],
        "research_only": True,
        "investment_authority": False,
    }
