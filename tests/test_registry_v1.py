from app.agent_registry import build_default_registry


def test_registry_v1_roster():
    assert len(build_default_registry().ids()) == 10
