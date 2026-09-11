"""API boundary for Capital Engine research entering the canonical analysis loop."""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.analysis_pipeline import run_analysis
from app.capital_engine import AlternativeDataRegistry, CapitalResearchRequest
from app.evidence_sources import SourceDocument, documents_to_evidence
from app.investment_domains import CapitalResearchDomain, CrossAssetLink, IntelligenceEntity, classify_cross_asset_links, cross_asset_hypotheses


class CrossAssetEntityModel(BaseModel):
    entity_id: str = Field(min_length=1, max_length=200)
    entity_type: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=500)
    geography: str | None = Field(default=None, max_length=300)
    attributes: Dict[str, Any] = Field(default_factory=dict)


class CrossAssetLinkModel(BaseModel):
    from_entity: CrossAssetEntityModel
    relationship: str = Field(min_length=1, max_length=200)
    to_entity: CrossAssetEntityModel
    evidence_ids: list[str] = Field(default_factory=list, max_length=100)


class CapitalResearchRequestModel(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    domains: list[CapitalResearchDomain] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list, max_length=100)
    documents: list[Dict[str, Any]] = Field(default_factory=list, max_length=200)
    cross_asset_links: list[CrossAssetLinkModel] = Field(default_factory=list, max_length=100)
    initial_value: float = Field(default=100.0, gt=0)
    horizon_steps: int = Field(default=60, ge=1, le=10000)
    paths: int = Field(default=5000, ge=100, le=100000)
    seed: int = Field(default=42, ge=0)


def _documents(values: list[Dict[str, Any]]) -> list[SourceDocument]:
    return [SourceDocument(**value) for value in values]


def _cross_asset_links(values: list[CrossAssetLinkModel]) -> list[CrossAssetLink]:
    return [CrossAssetLink(from_entity=IntelligenceEntity(**link.from_entity.model_dump()), relationship=link.relationship, to_entity=IntelligenceEntity(**link.to_entity.model_dump()), evidence_ids=link.evidence_ids) for link in values]


def build_capital_router(registry: AlternativeDataRegistry | None = None) -> APIRouter:
    """Expose research-only Capital Engine entry points.

    Providers remain optional. Normalized documents are evidence; cross-asset
    relationships are supplied as non-evidentiary research context and enter the
    canonical reasoning loop without being promoted to evidence.
    """
    router = APIRouter(prefix="/capital", tags=["capital-engine"])
    provider_registry = registry or AlternativeDataRegistry()

    @router.get("/manifest")
    def manifest() -> Dict[str, Any]:
        from app.capital_engine import capital_engine_manifest
        result = capital_engine_manifest()
        result["registered_providers"] = provider_registry.names()
        return result

    @router.post("/research")
    def research(request: CapitalResearchRequestModel) -> Dict[str, Any]:
        try:
            capital_request = CapitalResearchRequest(question=request.question, domains=request.domains, entities=request.entities)
            documents = _documents(request.documents)
            if not documents and provider_registry.names():
                packet = provider_registry.acquire(capital_request)
                documents = packet.documents
                providers = packet.provider_names
            else:
                providers = provider_registry.names() if documents else []

            evidence = documents_to_evidence(documents, claim=request.question)
            cross_asset_links = _cross_asset_links(request.cross_asset_links)
            evidence_ids = [item["evidence_id"] for item in evidence]
            hypotheses = cross_asset_hypotheses(cross_asset_links, evidence_ids)
            research_context = {
                "cross_asset_links": classify_cross_asset_links(cross_asset_links, evidence_ids),
                "research_hypotheses": [
                    {
                        "hypothesis_id": hypothesis.hypothesis_id,
                        "statement": hypothesis.statement,
                        "domain": hypothesis.domain.value,
                        "research_domains": hypothesis.research_domains,
                        "evidence_ids": hypothesis.evidence_ids,
                        "assumptions": hypothesis.assumptions,
                        "invalidation_conditions": hypothesis.invalidation_conditions,
                        "research_questions": hypothesis.research_questions,
                        "epistemic_stage": "hypothesis",
                    }
                    for hypothesis in hypotheses
                ],
            }
            result = run_analysis(question=request.question, evidence=evidence, initial_value=request.initial_value, horizon_steps=request.horizon_steps, paths=request.paths, seed=request.seed, research_context=research_context)
            result["capital_engine"] = {"domains": [domain.value for domain in request.domains], "entities": request.entities, "provider_names": providers, "document_count": len(documents), "cross_asset_links": research_context["cross_asset_links"], "research_hypotheses": research_context["research_hypotheses"], "research_only": True}
            return result
        except (TypeError, ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router
