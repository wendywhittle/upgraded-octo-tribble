from app.main import app


def test_learning_and_resolution_routes_are_registered():
    paths = {getattr(route, "path", None) for route in app.routes}
    assert "/observer/learning" in paths
    assert "/predictions/resolve" in paths
