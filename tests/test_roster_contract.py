from app.agent_registry import build_default_registry


def test_registered_roster_is_non_executable():
    registry = build_default_registry()
    assert len(registry.ids()) == 10
