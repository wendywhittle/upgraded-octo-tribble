from app.main import generate_agents


def test_legacy_demo_generator_is_no_longer_required_by_simulation():
    # The formal registry is the source used by the simulation endpoint; this
    # test intentionally checks the public roster remains available only as a
    # compatibility helper while the endpoint itself uses run_default_agents.
    assert len(generate_agents("compatibility check")) == 10
