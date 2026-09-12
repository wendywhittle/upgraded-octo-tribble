"""FastAPI endpoint for the Opportunity Acquisition Layer."""

from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.opportunity_acquisition import RawObservation, acquire


class OpportunityObservationRequest(BaseModel):
    source: str = Field(min_length=1, max_length=200)
    source_url: str = Field(default="", max_length=2000)
    observed_at: str = Field(default="", max_length=100)
    payload: Dict[str, Any] = Field(default_factory=dict)


class OpportunityAcquisitionRequest(BaseModel):
    observations: list[OpportunityObservationRequest] = Field(default_factory=list, max_length=200)


def build_opportunity_router() -> APIRouter:
    router = APIRouter(prefix="/opportunities", tags=["opportunity-acquisition"])

    @router.post("/acquire")
    def acquire_opportunities(request: OpportunityAcquisitionRequest) -> Dict[str, Any]:
        observations = [
            RawObservation(
                source=item.source.strip(),
                source_url=item.source_url.strip(),
                observed_at=item.observed_at.strip(),
                payload=item.payload,
            )
            for item in request.observations
        ]
        return acquire(observations)

    return router
