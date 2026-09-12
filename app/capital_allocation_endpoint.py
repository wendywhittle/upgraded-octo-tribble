"""API boundary for research-only capital allocation diagnostics."""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.capital_allocation import assess_allocation, capital_allocation_manifest


class AllocationPosition(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    weight: float = Field(ge=0, le=1)
    max_weight: float | None = Field(default=None, ge=0, le=1)


class AllocationRequest(BaseModel):
    positions: List[AllocationPosition] = Field(default_factory=list, max_length=200)
    gross_exposure: float | None = Field(default=None, ge=0)


def build_capital_allocation_router() -> APIRouter:
    router = APIRouter(prefix="/capital/allocation", tags=["capital-allocation"])

    @router.get("/manifest")
    def manifest() -> Dict[str, Any]:
        return capital_allocation_manifest()

    @router.post("/assess")
    def assess(request: AllocationRequest) -> Dict[str, Any]:
        try:
            return assess_allocation([item.model_dump() for item in request.positions], request.gross_exposure)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router
