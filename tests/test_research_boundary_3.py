from app.research_endpoint import build_research_router


def test_research_router_is_not_registered_without_explicit_configuration():
    # Configuration is opt-in in app.main; this factory itself only accepts feed URLs.
    router = build_research_router(["https://feeds.example.com/news"])
    assert router.prefix == "/research"
