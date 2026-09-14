from app.capital_epistemic import (
    EpistemicStatus,
    NormalizedObservation,
    UsageState,
    admit_evidence,
    build_evidence,
    knowledge_state,
    validate_observation,
)
from app.sec_edgar import SECClient, SECEDGARAdapter, SECRequestError, normalize_cik


USAGE = UsageState(
    retrievable=True,
    storable=True,
    transformable=True,
    displayable=True,
    retainable=True,
    redistributable=False,
)


SUBMISSIONS = {
    "name": "Example Holdings, Inc.",
    "tickers": [{"ticker": "EXM", "title": "Example Holdings, Inc."}],
    "exchanges": [{"exchange": "NYSE"}],
    "filings": {
        "recent": {
            "accessionNumber": ["0000123456-26-000001", "0000123456-26-000002"],
            "form": ["10-K", "10-K/A"],
            "filingDate": ["2026-02-20", "2026-03-01"],
            "reportDate": ["2025-12-31", "2025-12-31"],
            "acceptanceDateTime": [
                "2026-02-20T16:00:00.000Z",
                "2026-03-01T17:00:00.000Z",
            ],
            "primaryDocument": ["example-10k.htm", "example-10ka.htm"],
            "primaryDocDescription": ["10-K", "10-K/A"],
            "isXBRL": [1, 1],
        }
    },
}


COMPANY_CONCEPT = {
    "cik": 123456,
    "taxonomy": "us-gaap",
    "tag": "Revenues",
    "label": "Revenues",
    "description": "Revenue",
    "entityName": "Example Holdings, Inc.",
    "units": {
        "USD": [
            {
                "accn": "0000123456-26-000001",
                "fy": 2025,
                "fp": "FY",
                "form": "10-K",
                "filed": "2026-02-20",
                "start": "2025-01-01",
                "end": "2025-12-31",
                "val": 1000000,
                "uom": "USD",
                "decimals": "-3",
                "frame": "CY2025",
            },
            {
                "accn": "0000123456-26-000002",
                "fy": 2025,
                "fp": "FY",
                "form": "10-K/A",
                "filed": "2026-03-01",
                "start": "2025-01-01",
                "end": "2025-12-31",
                "val": 1100000,
                "uom": "USD",
                "decimals": "-3",
                "frame": "CY2025",
            },
        ]
    },
}


def adapter_with_responses():
    responses = {
        "/submissions/CIK0000123456.json": SUBMISSIONS,
        "/api/xbrl/companyconcept/CIK0000123456/us-gaap/Revenues.json": COMPANY_CONCEPT,
    }

    def fake_fetch(url, headers):
        assert headers["User-Agent"] == "Test Company test@example.com"
        for path, payload in responses.items():
            if url.endswith(path):
                return payload
        raise SECRequestError(f"unexpected URL: {url}")

    client = SECClient(
        "Test Company test@example.com",
        fake_fetch,
        min_request_interval=0,
    )
    return SECEDGARAdapter(
        client=client,
        base_url="https://data.sec.gov",
        clock=lambda: "2026-03-02T12:00:00+00:00",
    )


def test_normalize_cik_preserves_filer_identity():
    assert normalize_cik("123456") == "0000123456"
    assert normalize_cik(123456) == "0000123456"


def test_submissions_preserve_filing_identity_and_amendment():
    adapter = adapter_with_responses()
    metadata = adapter.submissions("123456")
    assert metadata["name"] == "Example Holdings, Inc."

    from app.sec_edgar import filing_metadata

    original = filing_metadata(metadata, "0000123456-26-000001")
    amended = filing_metadata(metadata, "0000123456-26-000002")
    assert original["form"] == "10-K"
    assert amended["form"] == "10-K/A"
    assert amended["amendment"] is True
    assert amended["primaryDocument"] == "example-10ka.htm"
    assert amended["acceptanceDateTime"] == "2026-03-01T17:00:00.000Z"


def test_cik_ticker_and_accession_are_separate_identity_layers():
    adapter = adapter_with_responses()
    observations = adapter.raw_observations(
        "123456", "us-gaap", "Revenues", submissions=SUBMISSIONS, usage=USAGE
    )
    assert observations
    subject = observations[0].subject
    assert subject.subject_id == "sec:cik:0000123456"
    assert subject.ticker == "EXM"
    assert subject.security_id is None
    assert subject.listing_id is None
    assert observations[0].revision_id == "0000123456-26-000001"


def test_xbrl_raw_fact_preserves_semantic_structure():
    adapter = adapter_with_responses()
    observations = adapter.raw_observations(
        "123456", "us-gaap", "Revenues", submissions=SUBMISSIONS, usage=USAGE
    )
    fact = observations[0].value
    assert fact["taxonomy"] == "us-gaap"
    assert fact["namespace"] == "us-gaap"
    assert fact["concept"] == "Revenues"
    assert fact["value"] == 1000000
    assert fact["unit"] == "USD"
    assert fact["decimals"] == "-3"
    assert fact["period"]["form"] == "duration"
    assert fact["period"]["start"] == "2025-01-01"
    assert fact["period"]["end"] == "2025-12-31"
    assert fact["fiscal"]["fp"] == "FY"
    assert fact["accession"] == "0000123456-26-000001"
    assert fact["amendment"] is False


def test_acceptance_is_not_silently_promoted_to_availability():
    adapter = adapter_with_responses()
    observations = adapter.raw_observations(
        "123456", "us-gaap", "Revenues", submissions=SUBMISSIONS, usage=USAGE
    )
    raw = observations[0]
    assert raw.published_at is None
    assert raw.available_at is None
    state = knowledge_state(raw, "2026-03-02T13:00:00+00:00")
    assert state.published_by_decision is False
    assert state.available_by_decision is False
    assert state.retrieved_by_decision is True
    assert state.knowable is False


def test_unknown_availability_fails_closed_for_evidence():
    adapter = adapter_with_responses()
    raw = adapter.raw_observations(
        "123456", "us-gaap", "Revenues", submissions=SUBMISSIONS, usage=USAGE
    )[0]
    normalized = NormalizedObservation(
        raw=raw,
        value=raw.value,
        unit="USD",
        currency="USD",
        transformation="identity",
    )
    validation = validate_observation(normalized)
    admission = admit_evidence(
        normalized,
        validation,
        "2026-03-02T13:00:00+00:00",
    )
    assert validation.status is EpistemicStatus.VALID
    assert admission.admitted is False
    assert admission.status is EpistemicStatus.INSUFFICIENT_EVIDENCE


def test_explicit_temporal_metadata_can_flow_into_existing_contract():
    adapter = adapter_with_responses()
    raw = adapter.raw_observations(
        "123456",
        "us-gaap",
        "Revenues",
        submissions=SUBMISSIONS,
        publication_at="2026-02-20T16:01:00+00:00",
        available_at="2026-02-20T16:02:00+00:00",
        usage=USAGE,
    )[0]
    normalized = NormalizedObservation(
        raw=raw,
        value=raw.value,
        unit="USD",
        currency="USD",
        transformation="identity",
    )
    validation = validate_observation(normalized)
    admission = admit_evidence(
        normalized,
        validation,
        "2026-02-21T00:00:00+00:00",
    )
    evidence = build_evidence(normalized, validation, admission)
    assert admission.admitted is True
    assert evidence.execution_authority is False
    assert evidence.provenance["source"] == "sec-edgar"
    assert evidence.provenance["accession"] == "0000123456-26-000001"
    assert evidence.provenance["accepted_timestamp"] == "2026-02-20T16:00:00.000Z"


def test_amended_filing_remains_distinct_and_is_not_overwritten():
    adapter = adapter_with_responses()
    observations = adapter.raw_observations(
        "123456", "us-gaap", "Revenues", submissions=SUBMISSIONS, usage=USAGE
    )
    original, amended = observations
    assert original.revision_id != amended.revision_id
    assert original.value["value"] == 1000000
    assert amended.value["value"] == 1100000
    assert amended.value["amendment"] is True
    assert amended.revised_from_revision_id is None


def test_usage_restriction_flows_to_existing_fail_closed_contract():
    restricted = UsageState(
        retrievable=True,
        storable=False,
        transformable=True,
        displayable=True,
        retainable=False,
        redistributable=False,
    )
    adapter = adapter_with_responses()
    raw = adapter.raw_observations(
        "123456", "us-gaap", "Revenues", submissions=SUBMISSIONS, usage=restricted
    )[0]
    normalized = NormalizedObservation(
        raw=raw,
        value=raw.value,
        unit="USD",
        currency="USD",
        transformation="identity",
    )
    admission = admit_evidence(
        normalized,
        validate_observation(normalized),
        "2026-03-02T13:00:00+00:00",
    )
    assert admission.status is EpistemicStatus.REJECTED


def test_execution_authority_remains_false():
    adapter = adapter_with_responses()
    raw = adapter.raw_observations(
        "123456", "us-gaap", "Revenues", submissions=SUBMISSIONS, usage=USAGE,
        publication_at="2026-02-20T16:01:00+00:00",
        available_at="2026-02-20T16:02:00+00:00",
    )[0]
    normalized = NormalizedObservation(
        raw=raw,
        value=raw.value,
        unit="USD",
        currency="USD",
        transformation="identity",
    )
    validation = validate_observation(normalized)
    admission = admit_evidence(normalized, validation, "2026-02-21T00:00:00+00:00")
    evidence = build_evidence(normalized, validation, admission)
    assert evidence.execution_authority is False
