from app.research_endpoint import build_research_router


def test_research_router_is_explicitly_scoped():
    router = build_research_router(["https://feeds.example.com/news"])
    assert router.prefix == "/research"
    assert any(route.path == "/research/evidence" for route in router.routes)
    assert all(route.methods == {"POST"} for route in router.routes)
