from app.dashboard_platform import dashboard_authority_contract, dashboard_pipeline, load_dashboard_platform


def test_dashboard_source_of_truth_is_canonical():
    contract = load_dashboard_platform()
    assert contract["platform_id"] == "aletheia_telos_interactive_dashboard"
    assert contract["status"] == "canonical"
    assert contract["identity"]["brand"] == "ALETHEIA TELOS"


def test_dashboard_pipeline_has_exact_canonical_order():
    pipeline = dashboard_pipeline()
    assert len(pipeline) == 11
    assert [stage["label"] for stage in pipeline] == [
        "OPPORTUNITY",
        "EVIDENCE",
        "UNDERWRITING",
        "PERSPECTIVES",
        "CONFLICT",
        "INDEPENDENT RISK",
        "CONTRARIAN",
        "INVESTMENT CASE",
        "DECISION GATE",
        "OBSERVER",
        "LEARNING",
    ]
    assert [stage["number"] for stage in pipeline] == list(range(1, 12))


def test_dashboard_preserves_human_authority_boundary():
    contract = dashboard_authority_contract()
    assert contract["dashboard_is_interactive"] is True
    assert contract["pipeline_stages_are_navigable"] is True
    assert contract["ready_for_human_authority_is_not_authorization"] is True
    assert contract["no_autonomous_execution"] is True
    assert contract["no_brokerage"] is True
    assert contract["no_capital_transfer"] is True
    assert contract["no_portfolio_mutation"] is True
