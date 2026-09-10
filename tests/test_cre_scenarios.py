from app.cre_scenarios import CREScenario, default_scenario_specs


def test_required_scenarios_exist_without_fake_values():
    specs = default_scenario_specs()
    assert {s.scenario for s in specs} == set(CREScenario)
    assert all(s.assumptions == () for s in specs)
    assert all(s.simulation_reference is None for s in specs)
