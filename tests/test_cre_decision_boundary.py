from app.cre_decision import build_decision_record
from app.cre_underwriting import Assumption, Property, UnderwritingDecision, UnderwritingInputs, underwrite


def test_no_deal_and_insufficient_evidence_are_distinct():
    insufficient = underwrite(UnderwritingInputs(
        opportunity_id="opp-1",
        property=Property("p-1", "industrial", "Vancouver, WA"),
        purchase_price=None,
        annual_noi=700_000,
    ))
    no_deal = underwrite(UnderwritingInputs(
        opportunity_id="opp-2",
        property=Property("p-2", "industrial", "Vancouver, WA"),
        purchase_price=10_000_000,
        annual_noi=500_000,
        no_deal_reasons=("Downside exceeds acceptable margin of safety.",),
    ))
    assert insufficient.decision == UnderwritingDecision.INSUFFICIENT_EVIDENCE
    assert no_deal.decision == UnderwritingDecision.NO_DEAL
    assert build_decision_record(insufficient).human_decision_required is True
    assert build_decision_record(no_deal).autonomous_execution is False
