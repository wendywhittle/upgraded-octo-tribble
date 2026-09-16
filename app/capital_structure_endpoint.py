"""Read-only API boundary for capital-structure analysis."""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.capital_structure import build_capital_structure_scenario, compare_capital_structures


def build_capital_structure_router() -> APIRouter:
    router = APIRouter(prefix="/capital-structure", tags=["capital-structure"])

    @router.post("/analyze")
    def analyze(request: Dict[str, Any]) -> Dict[str, Any]:
        """Compare explicitly supplied capital structures without recommending one."""
        scenarios = request.get("scenarios") or []
        if not scenarios:
            raise HTTPException(status_code=400, detail="scenarios must contain at least one analytical scenario")
        try:
            built = [
                build_capital_structure_scenario(
                    scenario_id=str(item["scenario_id"]),
                    label=str(item["label"]),
                    financing_evidence=item["financing_evidence"],
                    property_value=item.get("property_value"),
                    total_project_cost=item.get("total_project_cost"),
                    assumptions=item.get("assumptions"),
                )
                for item in scenarios
            ]
            return compare_capital_structures(built)
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router
