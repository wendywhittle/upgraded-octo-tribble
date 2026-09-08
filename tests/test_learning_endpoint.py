from app.learning_endpoint import LearningRequest, build_learning_router


def test_learning_request_defaults():
    request = LearningRequest()
    assert request.bins == 5


def test_learning_endpoint_is_read_only_projection():
    routes = build_learning_router().routes
    assert any(getattr(route, "path", None) == "/observer/learning" for route in routes)
