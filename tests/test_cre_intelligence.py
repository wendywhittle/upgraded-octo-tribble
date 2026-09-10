from app.cre_intelligence import CREDecision, CREOpportunity, screen


def test_missing_evidence_prevents_false_approval():
    result = screen(CREOpportunity("x", "industrial", "Vancouver, WA", asking_price=2_000_000))
    assert result.decision is CREDecision.INSUFFICIENT_EVIDENCE
    assert "noi" in result.missing_evidence
    assert "occupancy" in result.missing_evidence


def test_screening_never_returns_act():
    result = screen(
        CREOpportunity(
            "x", "industrial", "Vancouver, WA",
            asking_price=2_000_000, noi=140_000, occupancy=0.95,
        )
    )
    assert result.decision is CREDecision.WATCH
    assert "Screening is not investment approval." in result.reasons
