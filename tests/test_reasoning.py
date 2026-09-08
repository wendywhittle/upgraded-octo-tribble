from app.reasoning import build_reasoning_context, reason_from_evidence


def test_reasoning_context_preserves_only_usable_evidence():
    evidence = [
        {"evidence_id": "a", "claim": "verified", "decision_usable": True},
        {"evidence_id": "b", "claim": "blocked", "decision_usable": False},
    ]
    context = build_reasoning_context(evidence)
    assert context["evidence_count"] == 1
    assert context["blocked_evidence_count"] == 1
    assert context["evidence"][0]["evidence_id"] == "a"
    assert context["execution_capability"] is False


def test_reasoning_without_usable_evidence_forces_no_data():
    result = reason_from_evidence(
        "quant", "Is the opportunity attractive?",
        [{"evidence_id": "x", "claim": "blocked", "decision_usable": False}],
        "The thesis cannot be assessed from blocked evidence.",
        direction="LONG", confidence=0.8,
    )
    assert result["direction"] == "NO_DATA"
    assert result["confidence"] == 0.0
    assert result["reasoning_applied"] is True
    assert result["brokerage_connectivity"] is False
    assert result["human_decision_required"] is True


def test_reasoning_rejects_invalid_confidence_and_direction():
    evidence = [{"evidence_id": "a", "claim": "verified", "decision_usable": True}]
    for kwargs in ({"confidence": 1.1}, {"direction": "BUY"}):
        try:
            reason_from_evidence("q", "question", evidence, "thesis", **kwargs)
            assert False
        except ValueError:
            pass
