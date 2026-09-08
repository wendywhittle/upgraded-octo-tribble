from app.research import research_query


def test_research_result_marks_reasoning_as_not_applied():
    class EmptySource:
        name = "test"
        def acquire(self, query, limit=10):
            return []

    result = research_query(EmptySource(), "market", "A claim")
    assert result["reasoning_applied"] is False
