from app.epistemic_adapter import (
    learning_to_epistemic_records,
    observer_to_epistemic_record,
    prediction_to_epistemic_records,
    resolution_to_epistemic_records,
)


def test_prediction_maps_to_hypothesis_and_assumption_without_mutation():
    prediction = {
        "prediction_id": "pred-001",
        "question": "Will occupancy stabilize?",
        "predicted_probability": 0.8,
        "agent_id": "quant",
        "model_version": "test-model",
        "recorded_at": "2026-09-11T10:00:00+00:00",
        "evidence": [{"evidence_id": "E1"}],
        "assumptions": ["Lease rollover remains stable"],
    }
    records = prediction_to_epistemic_records(prediction)
    assert [record.record_type for record in records] == ["hypothesis", "assumption"]
    assert records[0].record_id == "hypothesis:pred-001"
    assert records[1].related_record_ids == ["hypothesis:pred-001"]


def test_resolution_maps_outcome_and_attribution_separately():
    resolution = {
        "prediction_id": "pred-001",
        "predicted_probability": 0.8,
        "outcome": True,
        "brier_error": 0.04,
        "resolved_at": "2026-09-12T10:00:00+00:00",
        "outcome_source": "verified-source",
    }
    records = resolution_to_epistemic_records(resolution)
    assert [record.record_type for record in records] == ["outcome", "attribution"]
    assert records[0].related_record_ids == ["hypothesis:pred-001"]
    assert records[1].related_record_ids == ["hypothesis:pred-001", "outcome:pred-001"]
    assert records[1].content["brier_error"] == 0.04


def test_observer_maps_to_interpretation_and_has_no_authority():
    observer = {
        "status": "observed",
        "question": "Test question",
        "agent_count": 3,
        "outcome_status": "pending",
        "learning_status": "awaiting_outcome",
        "synthesis_verdict": "HOLD",
    }
    record = observer_to_epistemic_record(observer)
    assert record.record_type == "interpretation"
    assert record.content["synthesis_verdict"] == "HOLD"
    assert record.has_authority is False


def test_existing_lessons_map_without_creating_new_learning_logic():
    records = learning_to_epistemic_records(
        {"lessons": [{"type": "overconfidence", "agent_id": "quant", "sample_count": 3, "gap": 0.2}]}
    )
    assert len(records) == 1
    assert records[0].record_type == "lesson"
    assert records[0].content["type"] == "overconfidence"
