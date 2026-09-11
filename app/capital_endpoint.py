"""API boundary for Capital Engine research entering the canonical analysis loop."""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.analysis_pipeline import run_analysis
from app.capital_engine import AlternativeDataRegistry, CapitalResearchRequest
from app.evidence_sources import SourceDocument, documents_to_evidence
from app.investment_domains import CapitalResearchDomain


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


def build_capital_router(registry: AlternativeDataRegistry | None = None) -> APIRouter:
    """Expose research-only Capital Engine entry points.

    Providers remain optional. The endpoint accepts normalized documents directly so
    the Capital Engine can be exercised without a paid data dependency.

    Cross-asset links are contextual research structure only. They do not become
    evidence unless explicitly backed by evidence IDs supplied in the request.
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
            capital_request = CapitalResearchRequest(
                question=request.question,
                domains=request.domains,
                entities=request.entities,
            )
            documents = _documents(request.documents)
            if not documents and provider_registry.names():
                packet = provider_registry.acquire(capital_request)
                documents = packet.documents
                providers = packet.provider_names
            else:
                providers = provider_registry.names() if documents else []

            evidence = documents_to_evidence(documents, claim=request.question)
            result = run_analysis(
                question=request.question,
                evidence=evidence,
                initial_value=request.initial_value,
                horizon_steps=request.horizon_steps,
                paths=request.paths,
                seed=request.seed,
            )
            result["capital_engine"] = {
                "domains": [domain.value for domain in request.domains],
                "entities": request.entities,
                "provider_names": providers,
                "document_count": len(documents),
                "cross_asset_links": [link.model_dump() for link in request.cross_asset_links],
                "research_only": True,
            }
            return result
        except (TypeError, ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router
