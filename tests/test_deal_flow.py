import os
import tempfile

import pytest

from app.deal_flow import create_deal, get_deal, underwrite, update_status


@pytest.fixture
def db_path(monkeypatch):
    with tempfile.TemporaryDirectory() as d:
        monkeypatch.setenv("ALETHEIA_DB_PATH", os.path.join(d, "deals.db"))
        yield


def test_explicit_noi_drives_cap_rate(db_path):
    result = underwrite({"purchase_price": 10_000_000, "noi": 650_000})
    assert result["derived"]["cap_rate"] == pytest.approx(0.065)


def test_noi_can_be_derived_from_egi_and_expenses(db_path):
    result = underwrite({"purchase_price": 10_000_000, "egi": 900_000, "operating_expenses": 250_000})
    assert result["derived"]["cap_rate"] == pytest.approx(0.065)


def test_missing_inputs_are_not_zeroed(db_path):
    result = underwrite({"purchase_price": 10_000_000})
    assert "cap_rate" not in result["derived"]
    assert "noi" in result["missing"]


def test_financing_is_deterministic(db_path):
    deal = {"purchase_price": 10_000_000, "noi": 650_000, "ltv": .7, "interest_rate": .065, "amortization_years": 30}
    assert underwrite(deal) == underwrite(deal)


def test_deal_record_preserves_inputs(db_path):
    record = create_deal({"name": "Test", "asset_type": "Industrial", "location": "Dallas", "purchase_price": 10_000_000, "noi": 650_000})
    assert record["original_inputs"]["purchase_price"] == 10_000_000
    assert get_deal(record["deal_id"])["original_inputs"]["noi"] == 650_000


def test_status_changes_are_explicit(db_path):
    record = create_deal({"name": "Test", "asset_type": "Industrial", "location": "Dallas", "purchase_price": 10_000_000, "noi": 650_000})
    updated = update_status(record["deal_id"], "HOLD")
    assert updated["status"] == "HOLD"
