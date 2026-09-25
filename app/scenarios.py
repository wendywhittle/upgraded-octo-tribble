"""Scenario analysis: base / bull / bear (+ custom) scenarios.

Each scenario reuses the existing underwrite() — no duplicated math. A
scenario is a named set of input overrides applied to the deal's submitted
inputs; the definition is stored alongside the computed result so every
number traces to the assumptions that produced it (Charter §12/§13).

Default bull/bear rules are documented below and labeled as scenario
assumptions, not forecasts:
  bull: effective NOI x1.10, exit cap -50bps (floor 50bps),
        interest rate -50bps (floor 10bps), hold +2 years
  bear: effective NOI x0.90, exit cap +50bps,
        interest rate +50bps, hold -2 years (floor 1)

Uncertainty (Charter §2.3): an input may be given as a [low, high] range.
When any input is a range, outputs are reported as [min, max] intervals
evaluated over every corner combination of the ranges — never as a point
estimate pretending the uncertainty away. Corner evaluation is documented
as a bound, not a distribution; distributions belong to simulation.
"""

from __future__ import annotations

import itertools
import math
import sqlite3
from datetime import datetime, timezone
from typing import Any

from app.deal_flow import underwrite

BULL_NOI_MULT = 1.10
BEAR_NOI_MULT = 0.90
RATE_BPS_SHIFT = 0.005
HOLD_YEAR_SHIFT = 2


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS scenarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id TEXT NOT NULL,
            name TEXT NOT NULL,
            definition TEXT NOT NULL,
            result TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_scenarios_deal ON scenarios(deal_id)")


def as_range(value: Any) -> tuple[float, float] | None:
    """Return (low, high) if value is a [low, high] range, else None."""
    if isinstance(value, (list, tuple)) and len(value) == 2:
        lo, hi = value
        if isinstance(lo, (int, float)) and isinstance(hi, (int, float)):
            if math.isfinite(lo) and math.isfinite(hi) and lo <= hi:
                return (float(lo), float(hi))
            raise ValueError(f"Invalid range {value!r}: need [low, high] with low <= high.")
    return None


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def underwrite_range(inputs: dict[str, Any]) -> dict[str, Any]:
    """Underwrite with ranged inputs via corner evaluation.

    Returns {"derived": {metric: scalar | [lo, hi]}, "missing": [...],
    "ranged": bool, "corners_evaluated": int}. Scalar-only inputs return the
    plain underwrite() shape with "ranged": False.
    """
    ranged_keys = [k for k, v in inputs.items() if as_range(v) is not None]
    if not ranged_keys:
        result = underwrite(inputs)
        return {"derived": result["derived"], "missing": result["missing"],
                "ranged": False, "corners_evaluated": 1}
    corners = list(itertools.product(*[as_range(inputs[k]) for k in ranged_keys]))
    derived_sets: list[dict[str, Any]] = []
    missing_sets: list[list[str]] = []
    for corner in corners:
        point = dict(inputs)
        for key, val in zip(ranged_keys, corner):
            point[key] = val
        out = underwrite(point)
        derived_sets.append(out["derived"])
        missing_sets.append(out["missing"])
    metrics: dict[str, Any] = {}
    keys = {k for d in derived_sets for k in d}
    for key in sorted(keys):
        vals = [d[key] for d in derived_sets if _is_number(d.get(key))]
        if vals and len(vals) == len(derived_sets):
            lo, hi = min(vals), max(vals)
            metrics[key] = [lo, hi] if lo != hi else lo
        # metrics absent in some corners stay absent: never invent them
    missing = sorted({m for s in missing_sets for m in s})
    return {"derived": metrics, "missing": missing,
            "ranged": True, "corners_evaluated": len(corners),
            "ranged_inputs": ranged_keys,
            "note": "Intervals are min/max over corner combinations of the input ranges; not a probability distribution."}


def _effective_noi(inputs: dict[str, Any]) -> tuple[str, float] | None:
    """Return (input_key_to_vary, base_value) for scenario NOI shifts."""
    noi = inputs.get("noi")
    if _is_number(noi):
        return ("noi", float(noi))
    egi, exp = inputs.get("egi"), inputs.get("operating_expenses")
    if _is_number(egi) and _is_number(exp):
        # Vary EGI; expenses held fixed. Documented simplification.
        return ("egi", float(egi))
    return None


def default_scenarios(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    """Build base/bull/bear definitions with documented shift rules."""
    defs = [{"name": "base", "overrides": {}, "notes": "Inputs as submitted."}]
    lever = _effective_noi(inputs)
    for name, mult, rate_sign, hold_sign in (
        ("bull", BULL_NOI_MULT, -1, +1),
        ("bear", BEAR_NOI_MULT, +1, -1),
    ):
        overrides: dict[str, Any] = {}
        notes: list[str] = []
        if lever:
            key, base_val = lever
            # Preserve ranges: shift both ends.
            rng = as_range(inputs[key])
            if rng:
                overrides[key] = [rng[0] * mult, rng[1] * mult]
            else:
                overrides[key] = base_val * mult
            notes.append(f"{key} x{mult} (scenario assumption, not a forecast)")
        else:
            notes.append("No NOI lever available (no NOI, EGI+expenses); NOI not varied.")
        for key, floor in (("exit_cap_rate", 0.005), ("interest_rate", 0.001)):
            val = inputs.get(key)
            rng = as_range(val)
            if rng:
                shifted = [max(floor, rng[0] + rate_sign * RATE_BPS_SHIFT),
                           max(floor, rng[1] + rate_sign * RATE_BPS_SHIFT)]
                overrides[key] = shifted
            elif _is_number(val):
                overrides[key] = max(floor, float(val) + rate_sign * RATE_BPS_SHIFT)
            if key in overrides:
                notes.append(f"{key} {'-' if rate_sign < 0 else '+'}50bps (floor {floor:.1%})")
        hold = inputs.get("hold_years")
        if _is_number(hold):
            overrides["hold_years"] = max(1, float(hold) + hold_sign * HOLD_YEAR_SHIFT)
            notes.append(f"hold_years {'+' if hold_sign > 0 else '-'}{HOLD_YEAR_SHIFT}y")
        defs.append({"name": name, "overrides": overrides, "notes": " ".join(notes)})
    return defs


def run_scenarios(
    deal_inputs: dict[str, Any],
    scenario_defs: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Compute full underwriting outputs per scenario. Pure function."""
    defs = scenario_defs if scenario_defs is not None else default_scenarios(deal_inputs)
    results: list[dict[str, Any]] = []
    for definition in defs:
        name = definition.get("name", "unnamed")
        overrides = dict(definition.get("overrides") or {})
        scenario_inputs = dict(deal_inputs)
        scenario_inputs.update(overrides)
        computed = underwrite_range(scenario_inputs)
        results.append({
            "name": name,
            "definition": {"overrides": overrides, "notes": definition.get("notes", "")},
            "inputs_used": scenario_inputs,
            "derived": computed["derived"],
            "missing": computed["missing"],
            "ranged": computed["ranged"],
            "corners_evaluated": computed["corners_evaluated"],
        })
    return results


def save_scenarios(
    conn: sqlite3.Connection, deal_id: str, results: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    import json

    ensure_schema(conn)
    created = utc_now()
    saved: list[dict[str, Any]] = []
    for r in results:
        cur = conn.execute(
            "INSERT INTO scenarios (deal_id, name, definition, result, created_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (deal_id, r["name"], json.dumps(r["definition"]), json.dumps({
                "derived": r["derived"], "missing": r["missing"],
                "ranged": r["ranged"], "corners_evaluated": r["corners_evaluated"],
            }), created),
        )
        conn.commit()
        saved.append({"id": cur.lastrowid, "deal_id": deal_id, **r, "created_at": created})
    return saved


def list_scenarios(conn: sqlite3.Connection, deal_id: str) -> list[dict[str, Any]]:
    import json

    ensure_schema(conn)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, deal_id, name, definition, result, created_at"
        " FROM scenarios WHERE deal_id = ? ORDER BY created_at, id",
        (deal_id,),
    ).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        rec = dict(row)
        rec["definition"] = json.loads(rec["definition"])
        rec["result"] = json.loads(rec["result"])
        out.append(rec)
    return out
