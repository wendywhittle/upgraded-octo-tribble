import pytest

from app.cre_decision import CREDecisionRecord, build_decision_record
from app.cre_underwriting import UnderwritingDecision, UnderwritingResult


def result(state=UnderwritingDecision.NO_DEAL):
    return UnderwritingResult(state, None, reasons=("Margin of safety is insufficient.",), evidence_ids=("ev-1",))


def test_decision_record_preserves_no_deal_and_requires_human():
    record = build_decision_record(result(), ("Verify tenant rollover",))
    assert record.state is UnderwritingDecision.NO_DEAL
    assert record.human_decision_required is True
    assert record.autonomous_execution is False
    assert record.unresolved_questions == ("Verify tenant rollover",)


def test_decision_record_cannot_disable_human_authority():
    with pytest.raises(ValueError):
        CREDecisionRecord(UnderwritingDecision.ACT, "x", human_decision_required=False)


def test_decision_record_cannot_enable_execution():
    with pytest.raises(ValueError):
        CREDecisionRecord(UnderwritingDecision.ACT, "x", autonomous_execution=True)
