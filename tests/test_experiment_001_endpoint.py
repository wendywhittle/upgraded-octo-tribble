from fastapi.testclient import TestClient

from app.main import app


def test_experiment_001_route_is_registered():
    paths = {route.path for route in app.routes}
    assert "/experiments/EXP-001/run" in paths


def test_experiment_001_endpoint_rejects_empty_dataset():
    client = TestClient(app)
    response = client.post("/experiments/EXP-001/run", json={"csv_text": "observed_at,available_at,source_id,source_version,methodology_version,content_hash,spx_close,vix_close,skew_close\n"})
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]


def test_experiment_001_endpoint_rejects_missing_required_columns():
    client = TestClient(app)
    response = client.post("/experiments/EXP-001/run", json={"csv_text": "observed_at,spx_close\n2026-01-02T21:00:00+00:00,5000\n"})
    assert response.status_code == 400
    assert "required columns" in response.json()["detail"]
