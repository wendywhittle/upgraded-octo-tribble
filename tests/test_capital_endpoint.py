from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_capital_manifest_is_research_only():
    response = client.get("/capital/manifest")
    assert response.status_code == 200
    body = response.json()
    assert body["provider_agnostic"] is True
    assert body["execution"]["order_submission"] is False
    assert body["execution"]["investment_authority"] is False


def test_capital_research_accepts_normalized_documents():
    response = client.post(
        "/capital/research",
        json={
            "question": "What is the investment implication of this observed activity?",
            "domains": ["alternative_data", "public_markets"],
            "entities": ["TEST"],
            "documents": [
                {
                    "source": "test-provider",
                    "title": "Observed activity",
                    "content": "A disclosed contract was observed.",
                    "retrieved_at": "2026-09-11T00:00:00+00:00",
                    "observed_at": "2026-09-10T00:00:00+00:00",
                    "source_id": "test-1",
                    "provenance_type": "external",
                    "point_in_time": True,
                }
            ],
            "initial_value": 100,
            "horizon_steps": 5,
            "paths": 100,
            "seed": 7,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["capital_engine"]["document_count"] == 1
    assert body["capital_engine"]["research_only"] is True
    assert body["evidence"]["count"] == 1
    assert body["audit"]["research_only"] is True
    assert body["governance"]["autonomous_execution"] is False


def test_capital_research_does_not_require_a_provider():
    response = client.post(
        "/capital/research",
        json={
            "question": "Research without a configured external provider",
            "paths": 100,
            "horizon_steps": 2,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["capital_engine"]["provider_names"] == []
    assert body["capital_engine"]["document_count"] == 0
