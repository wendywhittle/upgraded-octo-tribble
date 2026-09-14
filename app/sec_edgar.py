"""Small, provider-bound SEC/EDGAR adapter for the Capital Engine epistemic contract.

This module deliberately stops at source acquisition and mechanical mapping into
``app.capital_epistemic``. It does not resolve securities, interpret facts, or
make investment decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
import time
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional
from urllib.parse import quote
from urllib.request import Request, urlopen

from app.capital_epistemic import RawObservation, Subject, UsageState

SEC_DATA_BASE = "https://data.sec.gov"
SEC_SOURCE_ID = "sec-edgar"
DEFAULT_TIMEOUT_SECONDS = 20
MIN_REQUEST_INTERVAL_SECONDS = 0.11


class SECAdapterError(RuntimeError):
    """Base error for deterministic SEC adapter failures."""


class SECRequestError(SECAdapterError):
    """Raised when an SEC request cannot be completed safely."""


@dataclass(frozen=True)
class SECClient:
    """Minimal SEC HTTP client with declared User-Agent and conservative pacing."""

    user_agent: str
    fetch_json: Callable[[str, Mapping[str, str]], Mapping[str, Any]]
    min_request_interval: float = MIN_REQUEST_INTERVAL_SECONDS

    def __post_init__(self) -> None:
        if not self.user_agent or not self.user_agent.strip():
            raise ValueError("SEC User-Agent must be declared")

    def get_json(self, url: str) -> Mapping[str, Any]:
        headers = {
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Accept": "application/json",
        }
        return self.fetch_json(url, headers)


def _default_fetch_json(url: str, headers: Mapping[str, str]) -> Mapping[str, Any]:
    request = Request(url, headers=dict(headers), method="GET")
    try:
        with urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            payload = response.read().decode("utf-8")
    except Exception as exc:  # urllib exposes several network/HTTP exception types.
        raise SECRequestError(f"SEC request failed: {url}") from exc
    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise SECRequestError("SEC response was not valid JSON") from exc
    if not isinstance(decoded, Mapping):
        raise SECRequestError("SEC response was not a JSON object")
    return decoded


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_cik(cik: str | int) -> str:
    digits = "".join(ch for ch in str(cik) if ch.isdigit())
    if not digits:
        raise ValueError("CIK must contain digits")
    return digits.zfill(10)


def _accession(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    return str(raw).strip()


def _filing_index(submissions: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    recent = submissions.get("filings", {}).get("recent", {})
    if not isinstance(recent, Mapping):
        return {}
    fields = (
        "accessionNumber",
        "form",
        "filingDate",
        "reportDate",
        "acceptanceDateTime",
        "primaryDocument",
        "primaryDocDescription",
        "isXBRL",
    )
    arrays = {field: recent.get(field, []) for field in fields}
    result: Dict[str, Dict[str, Any]] = {}
    accessions = arrays["accessionNumber"]
    if not isinstance(accessions, list):
        return result
    for index, accession in enumerate(accessions):
        if not accession:
            continue
        item = {
            field: arrays[field][index] if index < len(arrays[field]) else None
            for field in fields
        }
        form = str(item.get("form") or "")
        item["amendment"] = form.endswith("/A")
        result[str(accession)] = item
    return result


def filing_metadata(submissions: Mapping[str, Any], accession: str) -> Dict[str, Any]:
    normalized = _accession(accession)
    if normalized is None:
        raise ValueError("accession is required")
    item = _filing_index(submissions).get(normalized)
    if item is None:
        raise SECAdapterError(f"filing not found in submissions response: {normalized}")
    return dict(item)


def _fact_effective_period(fact: Mapping[str, Any]) -> Optional[str]:
    start = fact.get("start")
    end = fact.get("end")
    if start and end:
        return f"{start}/{end}"
    return str(end) if end else None


def _fact_observation_value(fact: Mapping[str, Any], taxonomy: str, concept: str) -> Dict[str, Any]:
    """Preserve the raw XBRL semantics instead of reducing concept to value."""
    return {
        "taxonomy": taxonomy,
        "namespace": taxonomy,
        "concept": concept,
        "value": fact.get("val"),
        "unit": fact.get("uom"),
        "decimals": fact.get("decimals"),
        "entity": fact.get("entityName"),
        "period": {
            "start": fact.get("start"),
            "end": fact.get("end"),
            "instant": fact.get("instant"),
            "form": "duration" if fact.get("start") and fact.get("end") else "instant" if fact.get("instant") else None,
        },
        "fiscal": {
            "fy": fact.get("fy"),
            "fp": fact.get("fp"),
            "frame": fact.get("frame"),
        },
        "dimensions": fact.get("dimensions", {}),
        "context": fact.get("context"),
        "accession": fact.get("accn"),
        "form": fact.get("form"),
        "filed": fact.get("filed"),
        "frame": fact.get("frame"),
        "amendment": str(fact.get("form") or "").endswith("/A"),
    }


def _subject(submissions: Mapping[str, Any], cik: str) -> Subject:
    tickers = submissions.get("tickers") or []
    exchanges = submissions.get("exchanges") or []
    ticker = tickers[0].get("ticker") if isinstance(tickers, list) and tickers else None
    exchange = exchanges[0].get("exchange") if isinstance(exchanges, list) and exchanges else None
    name = submissions.get("name") or f"SEC filer {cik}"
    return Subject(
        subject_id=f"sec:cik:{cik}",
        subject_type="sec_filer",
        provider_id=cik,
        ticker=ticker,
        exchange=exchange,
        identifiers={"cik": cik, "filer_name": str(name)},
    )


class SECEDGARAdapter:
    """Narrow SEC adapter that maps submissions/XBRL facts to raw observations."""

    name = "sec-edgar"

    def __init__(
        self,
        *,
        client: Optional[SECClient] = None,
        user_agent: Optional[str] = None,
        base_url: str = SEC_DATA_BASE,
        clock: Callable[[], str] = _utc_now,
    ) -> None:
        configured = user_agent or os.getenv("SEC_USER_AGENT")
        if not configured:
            raise ValueError("SEC_USER_AGENT must be configured")
        self.client = client or SECClient(configured, _default_fetch_json)
        self.base_url = base_url.rstrip("/")
        self.clock = clock
        self._last_request_at: Optional[float] = None

    def _get(self, path: str) -> Mapping[str, Any]:
        now = time.monotonic()
        if self._last_request_at is not None:
            remaining = self.client.min_request_interval - (now - self._last_request_at)
            if remaining > 0:
                time.sleep(remaining)
        self._last_request_at = time.monotonic()
        return self.client.get_json(f"{self.base_url}{path}")

    def submissions(self, cik: str | int) -> Mapping[str, Any]:
        normalized = normalize_cik(cik)
        return self._get(f"/submissions/CIK{normalized}.json")

    def company_concept(self, cik: str | int, taxonomy: str, concept: str) -> Mapping[str, Any]:
        normalized = normalize_cik(cik)
        return self._get(
            f"/api/xbrl/companyconcept/CIK{normalized}/{quote(taxonomy, safe='')}/{quote(concept, safe='')}.json"
        )

    def raw_observations(
        self,
        cik: str | int,
        taxonomy: str,
        concept: str,
        *,
        submissions: Optional[Mapping[str, Any]] = None,
        publication_at: Optional[str] = None,
        available_at: Optional[str] = None,
        usage: Optional[UsageState] = None,
    ) -> List[RawObservation]:
        normalized_cik = normalize_cik(cik)
        submission_data = submissions or self.submissions(normalized_cik)
        facts_data = self.company_concept(normalized_cik, taxonomy, concept)
        facts_by_unit = facts_data.get("units")
        if not isinstance(facts_by_unit, Mapping):
            raise SECAdapterError("SEC company-concept response has no usable units")

        subject = _subject(submission_data, normalized_cik)
        filing_map = _filing_index(submission_data)
        retrieval_at = self.clock()
        effective_usage = usage or UsageState(
            retrievable=True,
            storable=True,
            transformable=True,
            displayable=True,
            retainable=True,
            redistributable=False,
        )
        observations: List[RawObservation] = []
        for unit, facts in facts_by_unit.items():
            if not isinstance(facts, list):
                continue
            for fact in facts:
                if not isinstance(fact, Mapping):
                    continue
                accession = _accession(fact.get("accn"))
                metadata = filing_map.get(accession or "", {})
                effective_period = _fact_effective_period(fact)
                raw_value = _fact_observation_value(fact, taxonomy, concept)
                raw_fingerprint = json.dumps(raw_value, sort_keys=True, separators=(",", ":"))
                revision_id = accession
                revised_from = None
                if accession and metadata.get("amendment"):
                    revised_from = f"filing:{accession}"
                observations.append(
                    RawObservation(
                        source_id=f"{SEC_SOURCE_ID}:CIK{normalized_cik}:{accession or 'unknown'}:{taxonomy}:{concept}:{unit}",
                        subject=subject,
                        value=raw_value,
                        observed_at=None,
                        effective_period=effective_period,
                        published_at=publication_at,
                        available_at=available_at,
                        retrieved_at=retrieval_at,
                        revision_id=revision_id,
                        revised_from_revision_id=revised_from,
                        revision_at=metadata.get("acceptanceDateTime"),
                        usage=effective_usage,
                        raw_fingerprint=raw_fingerprint,
                    )
                )
        return observations

    def provenance(self, observation: RawObservation, *, endpoint: str, metadata: Mapping[str, Any]) -> Dict[str, Any]:
        value = observation.value if isinstance(observation.value, Mapping) else {}
        return {
            "source": SEC_SOURCE_ID,
            "endpoint": endpoint,
            "subject": observation.subject.identifiers,
            "cik": observation.subject.identifiers.get("cik"),
            "accession": value.get("accession"),
            "form": value.get("form") or metadata.get("form"),
            "filing_date": metadata.get("filingDate"),
            "accepted_timestamp": metadata.get("acceptanceDateTime"),
            "report_period": metadata.get("reportDate") or observation.effective_period,
            "document": metadata.get("primaryDocument"),
            "concept": value.get("concept"),
            "namespace": value.get("namespace"),
            "taxonomy": value.get("taxonomy"),
            "unit": value.get("unit"),
            "context": value.get("context"),
            "dimensions": value.get("dimensions"),
            "observed_at": observation.observed_at,
            "published_at": observation.published_at,
            "available_at": observation.available_at,
            "retrieved_at": observation.retrieved_at,
            "revision_id": observation.revision_id,
            "revised_from_revision_id": observation.revised_from_revision_id,
            "revision_at": observation.revision_at,
            "raw_fingerprint": observation.raw_fingerprint,
        }


def build_adapter(*, user_agent: Optional[str] = None) -> SECEDGARAdapter:
    """Build an adapter from explicit or environment-provided SEC credentials."""
    return SECEDGARAdapter(user_agent=user_agent)
