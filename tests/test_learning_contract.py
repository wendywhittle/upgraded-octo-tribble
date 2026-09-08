from app.learning import build_learning_report


def test_learning_never_changes_authority_or_weights():
    report = build_learning_report([])
    assert report["authority_changed"] is False
    assert report["weights_changed"] is False
    assert report["learning_mode"] == "informational_only"
    assert report["execution_capability"] is False
    assert report["brokerage_connectivity"] is False
    assert report["portfolio_mutation"] is False
