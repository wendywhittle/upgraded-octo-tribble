"""Tests for Charter-aligned capabilities.

Covers: evidence log, perspectives (dissent preserved), scenarios,
Monte Carlo simulation (determinism), decision journal + observer, and the
new API endpoints. The 6 original deal-flow tests must keep passing.
"""

import os
import tempfile

import pytest

from app import evidence, journal, perspectives, scenarios, simulation
from app.deal_flow import create_deal, update_status


@pytest.fixture
def db_path(monkeypatch, tmp_path):
    monkeypatch.setenv("ALETHEIA_DB_PATH", str(tmp_path / "deals.db"))
    yield


@pytest.fixture
def full_deal(db_path):
    return create_deal({
        "name": "Full Deal", "asset_type": "Industrial", "location": "Dallas, TX",
        "purchase_price": 10_000_000, "noi": 650_000,
        "ltv": 0.7, "interest_rate": 0.065, "amortization_years": 30,
        "hold_years": 5, "exit_cap_rate": 0.06, "closing_costs": 100_000,
    })


@pytest.fixture
def thin_deal(db_path):
    return create_deal({
        "name": "Thin Deal", "asset_type": "Land", "location": "Nowhere",
        "purchase_price": 1_000_000,
    })


def _conn():
    from app.deal_flow import connect
    return connect()


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

def test_evidence_roundtrip(db_path, full_deal):
    conn = _conn()
    evidence.add_evidence(conn, full_deal["deal_id"], "observed", "Rent roll reviewed.", source="PM report")
    evidence.add_evidence(conn, full_deal["deal_id"], "assumed", "NOI grows 2%/yr.")
    items = evidence.list_evidence(conn, full_deal["deal_id"])
    assert [i["type"] for i in items] == ["observed", "assumed"]
    assert items[0]["source"] == "PM report"
    conn.close()


def test_evidence_rejects_bad_type(db_path, full_deal):
    conn = _conn()
    with pytest.raises(ValueError):
        evidence.add_evidence(conn, full_deal["deal_id"], "vibes", "trust me")
    conn.close()


def test_evidence_rejects_empty(db_path, full_deal):
    conn = _conn()
    with pytest.raises(ValueError):
        evidence.add_evidence(conn, full_deal["deal_id"], "observed", "   ")
    conn.close()


# ---------------------------------------------------------------------------
# Perspectives
# ---------------------------------------------------------------------------

def test_all_lenses_produce_required_keys(db_path, full_deal):
    analyses = perspectives.analyze_deal(full_deal, [])
    assert set(analyses) == {"Bull", "Bear", "Quant", "Skeptic"}
    required = {"belief", "why", "supporting_evidence", "contradicting_evidence",
                "key_assumptions", "uncertainty", "what_would_change_conclusion"}
    for lens, analysis in analyses.items():
        assert required <= set(analysis), lens
        assert isinstance(analysis["belief"], str) and analysis["belief"]


def test_dissent_is_preserved_not_merged(db_path, full_deal):
    conn = _conn()
    evidence.add_evidence(conn, full_deal["deal_id"], "assumed", "Rents will grow 3%/yr.")
    items = evidence.list_evidence(conn, full_deal["deal_id"])
    analyses = perspectives.analyze_deal(full_deal, items)
    conn.close()
    assert analyses["Bull"]["belief"] != analyses["Bear"]["belief"]
    # Bear must steelman the bull case, Bull must name its killers
    assert analyses["Bear"]["contradicting_evidence"]
    assert analyses["Bull"]["contradicting_evidence"]


def test_quant_is_honest_when_incomplete(db_path, thin_deal):
    analyses = perspectives.analyze_deal(thin_deal, [])
    assert "incomplete" in analyses["Quant"]["belief"].lower()


def test_unknown_lens_rejected(db_path, full_deal):
    with pytest.raises(ValueError):
        perspectives.analyze_deal(full_deal, [], lenses=["Moon"])


def test_perspectives_persist_and_list(db_path, full_deal):
    conn = _conn()
    saved = perspectives.save_perspectives(conn, full_deal["deal_id"], perspectives.analyze_deal(full_deal, []))
    assert len(saved) == 4
    listed = perspectives.list_perspectives(conn, full_deal["deal_id"])
    assert {p["lens"] for p in listed} == {"Bull", "Bear", "Quant", "Skeptic"}
    assert all(isinstance(p["why"], list) for p in listed)
    conn.close()


def test_bear_computes_fragility(db_path, full_deal):
    analyses = perspectives.analyze_deal(full_deal, [])
    assert any("Break-even NOI" in w for w in analyses["Bear"]["why"])


def test_skeptic_audits_soft_evidence(db_path, full_deal):
    conn = _conn()
    evidence.add_evidence(conn, full_deal["deal_id"], "hypothesis", "Submarket is about to turn.")
    items = evidence.list_evidence(conn, full_deal["deal_id"])
    analyses = perspectives.analyze_deal(full_deal, items)
    assert any("hypothesis" in w for w in analyses["Skeptic"]["why"])
    conn.close()


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

def test_default_scenarios_bull_bear_ordering(db_path, full_deal):
    results = scenarios.run_scenarios(full_deal["original_inputs"])
    assert [r["name"] for r in results] == ["base", "bull", "bear"]
    caps = {r["name"]: r["derived"]["cap_rate"] for r in results}
    assert caps["bull"] >= caps["base"] >= caps["bear"]
    assert all(not r["ranged"] for r in results)


def test_custom_scenario_override_respected(db_path, full_deal):
    results = scenarios.run_scenarios(
        full_deal["original_inputs"],
        [{"name": "long-hold", "overrides": {"hold_years": 10}, "notes": ""}],
    )
    assert results[0]["inputs_used"]["hold_years"] == 10
    assert results[0]["definition"]["overrides"] == {"hold_years": 10}


def test_ranged_inputs_yield_intervals_not_points(db_path, full_deal):
    results = scenarios.run_scenarios(
        full_deal["original_inputs"],
        [{"name": "wide", "overrides": {"noi": [500_000, 700_000]}, "notes": ""}],
    )
    cap = results[0]["derived"]["cap_rate"]
    assert isinstance(cap, list) and len(cap) == 2
    assert cap[0] == pytest.approx(0.05) and cap[1] == pytest.approx(0.07)
    assert results[0]["ranged"] is True


def test_invalid_range_rejected():
    with pytest.raises(ValueError):
        scenarios.as_range([5, 3])


def test_scenarios_persist(db_path, full_deal):
    conn = _conn()
    results = scenarios.run_scenarios(full_deal["original_inputs"])
    saved = scenarios.save_scenarios(conn, full_deal["deal_id"], results)
    assert len(saved) == 3
    listed = scenarios.list_scenarios(conn, full_deal["deal_id"])
    assert [s["name"] for s in listed] == ["base", "bull", "bear"]
    conn.close()


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def test_simulation_is_deterministic(db_path, full_deal):
    ranges = {"noi": [500_000, 800_000], "exit_cap_rate": [0.05, 0.07]}
    a = simulation.simulate(full_deal["original_inputs"], ranges, n=500, seed=7)
    b = simulation.simulate(full_deal["original_inputs"], ranges, n=500, seed=7)
    assert a == b


def test_simulation_percentiles_ordered_and_bounded(db_path, full_deal):
    ranges = {"noi": [500_000, 800_000], "exit_cap_rate": [0.05, 0.07]}
    s = simulation.simulate(full_deal["original_inputs"], ranges, n=500, seed=1)
    for metric in ("irr", "equity_multiple", "cash_on_cash"):
        m = s["metrics"][metric]
        if m["n"]:
            assert m["p10"] <= m["p50"] <= m["p90"]
    assert 0 <= (s["p_irr_negative"] or 0) <= 1
    assert 0 <= (s["p_cash_on_cash_negative"] or 0) <= 1
    assert 0 <= s["frac_irr_uncomputable"] <= 1


def test_simulation_rejects_bad_config(db_path, full_deal):
    with pytest.raises(ValueError):
        simulation.simulate(full_deal["original_inputs"], {"noi": [1, 2]}, n=10)
    with pytest.raises(ValueError):
        simulation.simulate(full_deal["original_inputs"], {"nope": [1, 2]}, n=500)
    with pytest.raises(ValueError):
        simulation.simulate(full_deal["original_inputs"], {"noi": [5, 1]}, n=500)
    with pytest.raises(ValueError):
        simulation.simulate(full_deal["original_inputs"], {}, n=500)


def test_simulation_persists(db_path, full_deal):
    conn = _conn()
    summary = simulation.simulate(full_deal["original_inputs"], {"noi": [500_000, 800_000]}, n=200, seed=3)
    saved = simulation.save_simulation(conn, full_deal["deal_id"], {"n": 200, "seed": 3}, summary)
    assert saved["summary"]["n"] == 200
    listed = simulation.list_simulations(conn, full_deal["deal_id"])
    assert len(listed) == 1 and listed[0]["summary"]["seed"] == 3
    conn.close()


# ---------------------------------------------------------------------------
# Journal + observer
# ---------------------------------------------------------------------------

def test_thesis_requires_pursue_status(db_path, full_deal):
    conn = _conn()
    with pytest.raises(ValueError):
        journal.record_thesis(conn, full_deal["deal_id"], "Looks good.")
    conn.close()


def test_thesis_outcome_observer_flow(db_path, full_deal):
    conn = _conn()
    update_status(full_deal["deal_id"], "PURSUE")
    t = journal.record_thesis(
        conn, full_deal["deal_id"], "Value-add industrial at 6.5% cap.",
        key_assumptions=["NOI verified", "Rate locked"], expected_outcome="Close in 60 days.",
    )
    assert t["key_assumptions"] == ["NOI verified", "Rate locked"]
    journal.record_outcome(conn, full_deal["deal_id"], "Closed at 6.4% cap.", lesson="Verify rents before pursuing.")
    summary = journal.observer_summary(conn)
    assert summary["counts"] == {"theses_recorded": 1, "outcomes_recorded": 1,
                                 "lessons_recorded": 1, "theses_awaiting_outcome": 0}
    deal = summary["deals"][0]
    assert deal["thesis"]["thesis"].startswith("Value-add")
    assert deal["outcome"]["actual_outcome"].startswith("Closed")
    assert summary["lessons"][0]["lesson"] == "Verify rents before pursuing."
    conn.close()


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def _api_client(monkeypatch, tmp_path):
    monkeypatch.setenv("ALETHEIA_DB_PATH", str(tmp_path / "api.db"))
    import importlib
    import app.main as main_mod
    importlib.reload(main_mod)  # re-run migrate() against the temp DB
    from fastapi.testclient import TestClient
    return TestClient(main_mod.app)


def _api_deal(client):
    r = client.post("/api/deals", json={
        "name": "API Deal", "asset_type": "Industrial", "location": "Dallas, TX",
        "purchase_price": 10_000_000, "noi": 650_000, "ltv": 0.7,
        "interest_rate": 0.065, "amortization_years": 30,
        "hold_years": 5, "exit_cap_rate": 0.06,
    })
    assert r.status_code == 200
    return r.json()["deal_id"]


def test_api_evidence_flow(monkeypatch, tmp_path):
    client = _api_client(monkeypatch, tmp_path)
    deal_id = _api_deal(client)
    r = client.post(f"/api/deals/{deal_id}/evidence",
                    json={"type": "sourced", "source": "OM", "content": "Rent roll attached."})
    assert r.status_code == 200 and r.json()["type"] == "sourced"
    r = client.get(f"/api/deals/{deal_id}/evidence")
    assert len(r.json()) == 1
    r = client.post(f"/api/deals/{deal_id}/evidence", json={"type": "vibes", "content": "x"})
    assert r.status_code == 400
    assert client.get("/api/deals/AT-2099-000001/evidence").status_code == 404


def test_api_perspectives_flow(monkeypatch, tmp_path):
    client = _api_client(monkeypatch, tmp_path)
    deal_id = _api_deal(client)
    r = client.post(f"/api/deals/{deal_id}/perspectives", json={})
    assert r.status_code == 200 and len(r.json()) == 4
    r = client.post(f"/api/deals/{deal_id}/perspectives", json={"lenses": ["Bear"]})
    assert r.status_code == 200 and r.json()[0]["lens"] == "Bear"
    r = client.get(f"/api/deals/{deal_id}/perspectives")
    assert len(r.json()) == 5  # history preserved, never merged
    r = client.post(f"/api/deals/{deal_id}/perspectives", json={"lenses": ["Moon"]})
    assert r.status_code == 400


def test_api_scenarios_flow(monkeypatch, tmp_path):
    client = _api_client(monkeypatch, tmp_path)
    deal_id = _api_deal(client)
    r = client.post(f"/api/deals/{deal_id}/scenarios", json={})
    assert r.status_code == 200
    assert [s["name"] for s in r.json()] == ["base", "bull", "bear"]
    r = client.post(f"/api/deals/{deal_id}/scenarios", json={
        "scenarios": [{"name": "wide", "overrides": {"noi": [500000, 700000]}}]})
    assert isinstance(r.json()[0]["derived"]["cap_rate"], list)
    r = client.get(f"/api/deals/{deal_id}/scenarios")
    assert len(r.json()) == 4


def test_api_simulate_flow(monkeypatch, tmp_path):
    client = _api_client(monkeypatch, tmp_path)
    deal_id = _api_deal(client)
    r = client.post(f"/api/deals/{deal_id}/simulate",
                    json={"ranges": {"noi": [500000, 800000]}, "n": 200, "seed": 11})
    assert r.status_code == 200
    summary = r.json()["summary"]
    assert summary["metrics"]["irr"]["p10"] <= summary["metrics"]["irr"]["p90"]
    r = client.post(f"/api/deals/{deal_id}/simulate", json={"ranges": {}, "n": 200})
    assert r.status_code == 400
    r = client.get(f"/api/deals/{deal_id}/simulations")
    assert len(r.json()) == 1


def test_api_thesis_guard_and_observer(monkeypatch, tmp_path):
    client = _api_client(monkeypatch, tmp_path)
    deal_id = _api_deal(client)
    r = client.post(f"/api/deals/{deal_id}/thesis", json={"thesis": "Buy it."})
    assert r.status_code == 400  # not PURSUE yet
    r = client.patch(f"/api/deals/{deal_id}/status", json={"status": "PURSUE"})
    assert r.status_code == 200
    r = client.post(f"/api/deals/{deal_id}/thesis", json={
        "thesis": "Buy it.", "key_assumptions": ["Rents real"], "expected_outcome": "Close Q4."})
    assert r.status_code == 200
    r = client.post(f"/api/deals/{deal_id}/outcome",
                    json={"actual_outcome": "Closed.", "lesson": "Move faster next time."})
    assert r.status_code == 200
    r = client.get("/api/observer")
    assert r.status_code == 200
    body = r.json()
    assert body["counts"]["theses_recorded"] == 1
    assert body["lessons"][0]["lesson"] == "Move faster next time."
