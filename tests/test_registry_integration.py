from app.agent_registry import build_default_registry


def test_default_registry_has_ten_perspectives():
    assert len(build_default_registry().ids()) == 10
