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
    assert len(body["evidence"]["validation"]) == 1
    assert body["evidence"]["validation"][0]["decision_usable"] is True
    assert body["audit"]["research_only"] is True
    assert body["governance"]["autonomous_execution"] is False


def test_capital_research_classifies_cross_asset_context():
    response = client.post(
        "/capital/research",
        json={
            "question": "Could observed company activity affect industrial real assets?",
            "domains": ["alternative_data", "public_markets"],
            "entities": ["COMPANY", "INDUSTRIAL_ASSET"],
            "documents": [
                {
                    "source": "test-provider",
                    "title": "Observed activity",
                    "content": "A disclosed contract was observed.",
                    "retrieved_at": "2026-09-11T00:00:00+00:00",
                    "source_id": "evidence-1",
                    "provenance_type": "external",
                    "point_in_time": True,
                }
            ],
            "cross_asset_links": [
                {
                    "from_entity": {
                        "entity_id": "company-1",
                        "entity_type": "company",
                        "name": "Example Company",
                    },
                    "relationship": "drives_demand_for",
                    "to_entity": {
                        "entity_id": "asset-1",
                        "entity_type": "industrial_asset",
                        "name": "Example Industrial Asset",
                        "geography": "Pacific Northwest",
                    },
                    "evidence_ids": ["evidence-1"],
                }
            ],
            "paths": 100,
            "horizon_steps": 2,
        },
    )
    assert response.status_code == 200
    body = response.json()
    link = body["capital_engine"]["cross_asset_links"][0]
    assert link["relationship"] == "drives_demand_for"
    assert link["evidence_backed"] is True
    assert link["epistemic_stage"] == "evidence"
    assert link["missing_evidence_ids"] == []

    hypothesis = body["capital_engine"]["research_hypotheses"][0]
    assert hypothesis["epistemic_stage"] == "hypothesis"
    assert hypothesis["evidence_ids"] == ["evidence-1"]
    assert hypothesis["domain"] == "asset"
    assert hypothesis["research_questions"]

    context_hypothesis = body["research_context"]["research_hypotheses"][0]
    assert context_hypothesis == hypothesis
    assert body["research_context"]["cross_asset_links"][0]["epistemic_stage"] == "evidence"
    assert body["evidence"]["count"] == 1
    assert [item["evidence_id"] for item in body["agents"][0]["evidence"]] == ["evidence-1"]
    assert body["audit"]["research_context_supplied"] is True
    assert body["audit"]["research_only"] is True
    assert body["audit"]["human_decision_required"] is True


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
