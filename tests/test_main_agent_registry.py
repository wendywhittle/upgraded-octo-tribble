import app.main as main


def test_simulation_module_uses_formal_registry():
    source = main.simulate.__code__
    assert "run_default_agents" in source.co_names
