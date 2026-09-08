from app.learning import build_learning_report


def _resolution(agent_id, horizon, probability, outcome, prediction_id):
    return {
        "record_type": "prediction_resolution",
        "prediction_id": prediction_id,
        "agent_id": agent_id,
        "model_version": "test-v1",
        "horizon": horizon,
        "predicted_probability": probability,
        "outcome": outcome,
        "brier_error": round((probability - int(outcome)) ** 2, 6),
    }


def test_learning_reports_agent_and_horizon_metrics_without_authority_changes():
    records = [
        _resolution("quant", "medium", 0.8, True, "p1"),
        _resolution("quant", "medium", 0.8, False, "p2"),
        _resolution("quant", "long", 0.2, False, "p3"),
        _resolution("researcher", "long", 0.2, True, "p4"),
    ]
    report = build_learning_report(records)

    assert report["resolved_prediction_count"] == 4
    assert report["agent_metrics"]["quant"]["sample_count"] == 3
    assert "medium" in report["horizon_metrics"]
    assert report["authority_changed"] is False
    assert report["weights_changed"] is False
    assert report["historical_records_mutated"] is False
    assert report["research_only"] is True


def test_learning_flags_recurring_overconfidence_informationally():
    records = [
        _resolution("quant", "medium", 0.9, False, "p1"),
        _resolution("quant", "medium", 0.9, False, "p2"),
        _resolution("quant", "medium", 0.9, True, "p3"),
    ]
    report = build_learning_report(records)
    assert any(
        lesson["type"] == "overconfidence" and lesson["agent_id"] == "quant"
        for lesson in report["lessons"]
    )
    assert report["adaptation_policy"].startswith("No automatic")
