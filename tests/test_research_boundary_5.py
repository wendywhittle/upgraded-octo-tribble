from app.research import research_query


def test_research_requires_nonempty_query_and_claim():
    class EmptySource:
        name = "test"
        def acquire(self, query, limit=10):
            return []

    source = EmptySource()
    for query, claim in [("", "claim"), ("query", "")]:
        try:
            research_query(source, query, claim)
        except ValueError:
            pass
        else:
            raise AssertionError("empty research inputs must be rejected")
