from app.agent_registry import build_default_registry


def test_registry_has_ten_agents():
    assert len(build_default_registry().ids()) == 10
