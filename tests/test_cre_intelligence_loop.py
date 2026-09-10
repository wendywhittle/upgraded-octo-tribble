from app.conflict_intelligence import detect_cre_conflicts
from app.cre_adversarial import review_cre_simulation
from app.cre_context import CREOpportunityContext
from app.cre_kaleidoscope import CRE_PERSPECTIVES
from app.cre_perspectives import assess_cre_opportunity
from app.simulator import run_cre_monte_carlo


def make_context(**overrides):
    values = dict(
        opportunity_id="opp-1",
        property_id="prop-1",
        asset_type="industrial",
        location="Vancouver, WA",
        purchase_price=10_000_000,
        noi=700_000,
        occupancy=0.95,
        rent_growth=0.03,
        vacancy=0.05,
        interest_rate=0.06,
        hold_period=5,
        cap_rate=0.065,
        capital_expenditures=25_000,
        evidence=("lease-1", "rent-roll-1"),
        assumptions=("normalized NOI", "exit cap verified"),
    )
    values.update(overrides)
    return CREOpportunityContext(**values)


def test_same_opportunity_reaches_all_eight_perspectives():
    assessments = assess_cre_opportunity(make_context())
    assert tuple(a.perspective_id for a in assessments) == CRE_PERSPECTIVES
    assert all(a.opportunity_id == "opp-1" for a in assessments)


def test_perspectives_have_distinct_analytical_lenses():
    assessments = assess_cre_opportunity(make_context())
    theses = {a.perspective_id: a.thesis for a in assessments}
    assert len(set(theses.values())) == len(CRE_PERSPECTIVES)
    assert "permanent capital loss" in " ".join(assessments[7].risks).lower()
    assert "fragile" in assessments[6].thesis.lower()


def test_missing_inputs_are_preserved_and_not_fabricated():
    ctx = make_context(purchase_price=None, noi=None)
    assert "purchase_price" in ctx.missing_required()
    assert "noi" in ctx.missing_required()
    result = run_cre_monte_carlo(None, None)
    assert result["status"] == "INSUFFICIENT EVIDENCE"
    assert set(result["missing_inputs"]) == {"purchase_price", "noi"}


def test_cre_conflict_projection_preserves_disagreement_dimensions():
    assessments = list(assess_cre_opportunity(make_context()))
    assessments[0] = assessments[0].__class__(
        **{**assessments[0].__dict__, "assumptions": ("normalized NOI", "exit cap verified")}
    )
    assessments[1] = assessments[1].__class__(
        **{**assessments[1].__dict__, "assumptions": ("aggressive rent growth", "exit cap verified")}
    )
    conflicts = detect_cre_conflicts(assessments[:2])
    assert any(c["dimension"] == "assumptions" for c in conflicts)
    assert all(c["status"] == "unresolved" for c in conflicts)


def test_simulation_is_independent_and_has_all_required_scenarios():
    result = run_cre_monte_carlo(10_000_000, 700_000, hold_period=5, paths=200, seed=7)
    assert result["independent_of_agents"] is True
    assert {s["scenario"] for s in result["scenarios"]} == {"BASE", "BULL", "BEAR", "ADVERSARIAL", "TAIL RISK"}
    assert all("probability_loss" in s for s in result["scenarios"])


def test_adversarial_review_uses_simulation_results():
    simulation = run_cre_monte_carlo(10_000_000, 700_000, hold_period=5, paths=200, seed=7)
    review = review_cre_simulation(simulation, ("rent growth", "exit cap"), ("lease-1",))
    assert review.status == "reviewed"
    assert review.evidence_ids == ("lease-1",)
    assert review.challenges


def test_governance_remains_human_only():
    simulation = run_cre_monte_carlo(10_000_000, 700_000, paths=100, seed=1)
    review = review_cre_simulation(simulation)
    assert review.human_decision_required is True
