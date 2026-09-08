from app.prediction_resolution import resolve_prediction


def test_resolution_creates_separate_record_and_brier_error():
    prediction = {
        "prediction_id": "pred-123",
        "agent_id": "quant",
        "model_version": "test-model",
        "question": "Will outcome occur?",
        "predicted_probability": 0.8,
        "recorded_at": "2026-09-08T12:00:00+00:00",
    }
    result = resolve_prediction(
        prediction,
        True,
        "2026-09-09T12:00:00+00:00",
        "unit-test-source",
    )
    assert result["record_type"] == "prediction_resolution"
    assert result["prediction_id"] == "pred-123"
    assert result["brier_error"] == 0.04
    assert prediction["predicted_probability"] == 0.8
    assert result["historical_prediction_mutated"] is False
    assert result["research_only"] is True
    assert result["human_decision_required"] is True


def test_resolution_rejects_missing_probability():
    prediction = {"prediction_id": "pred-123"}
    try:
        resolve_prediction(prediction, True, "2026-09-09T12:00:00+00:00")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "predicted_probability" in str(exc)


def test_resolution_rejects_resolution_before_issuance():
    prediction = {
        "prediction_id": "pred-123",
        "predicted_probability": 0.5,
        "predicted_at": "2026-09-10T12:00:00+00:00",
    }
    try:
        resolve_prediction(prediction, False, "2026-09-09T12:00:00+00:00")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "precede" in str(exc)
