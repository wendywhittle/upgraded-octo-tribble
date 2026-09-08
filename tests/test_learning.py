from app.learning import build_learning_report


def test_learning_report_is_informational_and_agent_attributed():
    result = build_learning_report([
        {
            "record_type": "prediction_resolution",
            "prediction_id": "pred-a",
            "agent_id": "quant",
            "predicted_probability": 0.8,
            "outcome": True,
        },
        {
            "record_type": "prediction_resolution",
            "prediction_id": "pred-b",
            "agent_id": "contrarian",
            "predicted_probability": 0.2,
            "outcome": True,
        },
    ])
    assert result["resolved_prediction_count"] == 2
    assert result["agent_metrics"]["quant"]["brier_score"] == 0.04
    assert result["agent_metrics"]["contrarian"]["brier_score"] == 0.64
    assert result["authority_changed"] is False
    assert result["weights_changed"] is False
    assert result["historical_records_mutated"] is False
    assert result["research_only"] is True


def test_learning_report_ignores_non_resolution_records():
    result = build_learning_report([{"record_type": "decision_observation", "outcome": True}])
    assert result["resolved_prediction_count"] == 0
    assert result["status"] == "insufficient_data"
