from app.research_endpoint import build_research_router


def test_research_router_has_no_write_route():
    router = build_research_router(["https://feeds.example.com/news"])
    assert {method for route in router.routes for method in route.methods} == {"POST"}
