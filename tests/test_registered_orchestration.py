import app.main as main


def test_simulation_uses_formal_registry():
    assert "run_default_agents" in main.simulate.__code__.co_names
