from app.agent_registry import build_default_registry


def test_kaleidoscope_registry_count():
    assert len(build_default_registry().ids()) == 10
