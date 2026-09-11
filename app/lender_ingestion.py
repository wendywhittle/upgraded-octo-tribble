"""Structured ingestion boundary for externally supplied lender evidence.

This module validates and normalizes supplied records into the Phase 8A lender
intelligence contract. It does not scrape sources, resolve conflicts, calculate
financing consequences, select lenders, authorize capital, or execute actions.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from pydantic import ValidationError

from app.lender_intelligence import (
    FinancingTerms,
    LenderIntelligenceValidationError,
    LenderProfile,
    validate_financing_terms_collection,
    validate_lender_evidence,
)


class LenderEvidenceIngestionError(ValueError):
    """Raised when supplied lender evidence cannot cross the ingestion boundary."""


def ingest_lender_profile(payload: dict[str, Any]) -> LenderProfile:
    """Validate one externally supplied lender profile."""
    try:
        return LenderProfile.model_validate(deepcopy(payload))
    except ValidationError as exc:
        raise LenderEvidenceIngestionError(str(exc)) from exc


def ingest_financing_terms(payload: dict[str, Any]) -> FinancingTerms:
    """Validate one externally supplied financing-term record."""
    try:
        validate_lender_evidence([payload])
        return FinancingTerms.model_validate(deepcopy(payload))
    except (ValidationError, LenderIntelligenceValidationError) as exc:
        raise LenderEvidenceIngestionError(str(exc)) from exc


def ingest_financing_terms_collection(
    payloads: list[dict[str, Any]],
) -> list[FinancingTerms]:
    """Ingest a collection while preserving explicit conflicts."""
    try:
        validate_lender_evidence(payloads)
        terms = [FinancingTerms.model_validate(deepcopy(payload)) for payload in payloads]
        validate_financing_terms_collection(terms)
        return terms
    except (ValidationError, LenderIntelligenceValidationError) as exc:
        raise LenderEvidenceIngestionError(str(exc)) from exc


def capture_raw_lender_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    """Return an immutable-by-convention copy for a future source-capture layer.

    This deliberately performs no interpretation. A future scraper can use this
    boundary to preserve raw source material before structured ingestion.
    """
    return deepcopy(payload)
