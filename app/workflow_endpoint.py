from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.workflow import (
    ActorType,
    AuthorizationDecision,
    AuthorizationGate,
    Opportunity,
    WorkflowError,
    WorkflowService,
    WorkflowState,
)


class CreateDealRequest(BaseModel):
    name: str
    description: Optional[str] = None
    provenance: Dict[str, Any] = Field(default_factory=dict)


class TransitionRequest(BaseModel):
    new_state: WorkflowState
    actor: str
    actor_type: ActorType
    reason: str
    authorization_id: Optional[str] = None


class AuthorizationRequest(BaseModel):
    gate: AuthorizationGate
    decision: AuthorizationDecision
    actor: str
    actor_type: ActorType
    reason: str
    scope: Dict[str, Any] = Field(default_factory=dict)


def build_workflow_router(service: Optional[WorkflowService] = None) -> APIRouter:
    service = service or WorkflowService()
    router = APIRouter(prefix="/workflow", tags=["workflow"])

    @router.post("/deals", status_code=201)
    def create_deal(request: CreateDealRequest):
        deal = service.create_deal(Opportunity(name=request.name, description=request.description, provenance=request.provenance))
        return deal.model_dump(mode="json")

    @router.get("/deals/{deal_id}")
    def get_deal(deal_id: str):
        try:
            return service.get_deal(deal_id).model_dump(mode="json")
        except WorkflowError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/deals/{deal_id}/authorize")
    def authorize(deal_id: str, request: AuthorizationRequest):
        try:
            result = service.authorize(deal_id, request.gate, request.decision, request.actor,
                                      request.actor_type, request.reason, request.scope)
            return result.model_dump(mode="json")
        except WorkflowError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @router.post("/deals/{deal_id}/transition")
    def transition(deal_id: str, request: TransitionRequest):
        try:
            result = service.transition(deal_id, request.new_state, request.actor, request.actor_type,
                                        request.reason, request.authorization_id)
            return result.model_dump(mode="json")
        except WorkflowError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.get("/deals/{deal_id}/audit")
    def audit(deal_id: str):
        try:
            service.get_deal(deal_id)
            return {"deal_id": deal_id, "events": service.audit(deal_id)}
        except WorkflowError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return router
