import pytest

from app.cre_kaleidoscope import CRE_PERSPECTIVES, PerspectiveAssessment, empty_assessments


def test_all_required_cre_perspectives_are_represented():
    assert CRE_PERSPECTIVES == (
        "underwriter", "investor", "quant", "researcher", "macro", "systems", "contrarian", "risk"
    )
    assert {a.perspective_id for a in empty_assessments("deal-1")} == set(CRE_PERSPECTIVES)


def test_assessment_preserves_disagreement_fields():
    assessment = PerspectiveAssessment(
        "deal-1", "contrarian", "Tenant concentration creates fragility.",
        supporting_evidence=("ev-1",), contradictory_evidence=("ev-2",),
        assumptions=("renewal occurs",), confidence=0.7,
        invalidation_conditions=("tenant diversifies",), unanswered_questions=("lease options?",),
        evidence_ids=("ev-1", "ev-2"), audit_metadata=("run-1",),
    )
    assert assessment.contradictory_evidence == ("ev-2",)
    assert assessment.invalidation_conditions == ("tenant diversifies",)
    assert assessment.evidence_ids == ("ev-1", "ev-2")


def test_unknown_perspective_is_rejected():
    with pytest.raises(ValueError):
        PerspectiveAssessment("deal-1", "consensus", "x")


def test_confidence_is_bounded():
    with pytest.raises(ValueError):
        PerspectiveAssessment("deal-1", "risk", "x", confidence=-0.1)
