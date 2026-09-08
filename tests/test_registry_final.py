from app.agent_registry import build_default_registry


def test_registry_final_roster_size():
    assert len(build_default_registry().ids()) == 10
