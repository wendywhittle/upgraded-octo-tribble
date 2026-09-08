from app.research import research_query


def test_research_result_declares_no_execution_capability():
    class EmptySource:
        name = "test"
        def acquire(self, query, limit=10):
            return []

    result = research_query(EmptySource(), "market", "A claim")
    assert result["execution_capability"] is False
    assert result["order_capability"] is False
    assert result["brokerage_connectivity"] is False
