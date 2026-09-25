"""Monte Carlo risk simulation over user-supplied input ranges.

Draws n samples (seeded RNG: identical seed + inputs => identical results),
runs each through the existing underwrite(), and summarizes the distribution
of IRR, equity multiple, and cash-on-cash as p10/p50/p90 plus loss
probabilities.

Documented limitations (Charter §2.3: uncertainty must be visible):
  - draws are independent uniform per input; real inputs correlate
    (e.g. exit cap and interest rate). The summary therefore understates
    joint-tail risk.
  - a [low, high] range is a bound on belief, not a calibrated distribution.
"""

from __future__ import annotations

import math
import random
import sqlite3
from datetime import datetime, timezone
from typing import Any

from app.deal_flow import underwrite

KNOWN_INPUTS = (
    "purchase_price", "noi", "egi", "operating_expenses", "occupancy",
    "ltv", "interest_rate", "amortization_years", "hold_years",
    "exit_cap_rate", "closing_costs",
)

METRICS = ("irr", "equity_multiple", "cash_on_cash")

MIN_DRAWS = 100
MAX_DRAWS = 10000


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS simulations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id TEXT NOT NULL,
            config TEXT NOT NULL,
            summary TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_simulations_deal ON simulations(deal_id)")


def _percentile(sorted_vals: list[float], pct: float) -> float:
    """Linear-interpolation percentile; deterministic."""
    if not sorted_vals:
        raise ValueError("No values for percentile.")
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    rank = (pct / 100) * (len(sorted_vals) - 1)
    lo = math.floor(rank)
    hi = math.ceil(rank)
    if lo == hi:
        return sorted_vals[int(rank)]
    frac = rank - lo
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * frac


def simulate(
    deal_inputs: dict[str, Any],
    ranges: dict[str, list[float]],
    n: int = 1000,
    seed: int = 0,
) -> dict[str, Any]:
    """Run the Monte Carlo simulation. Pure function; deterministic in seed."""
    if not isinstance(n, int) or not (MIN_DRAWS <= n <= MAX_DRAWS):
        raise ValueError(f"n must be an int in [{MIN_DRAWS}, {MAX_DRAWS}].")
    if not ranges:
        raise ValueError("ranges must be non-empty: {input_name: [low, high]}.")
    clean: dict[str, tuple[float, float]] = {}
    for key, bounds in ranges.items():
        if key not in KNOWN_INPUTS:
            raise ValueError(f"Unknown input {key!r}; must be one of {KNOWN_INPUTS}.")
        if (not isinstance(bounds, (list, tuple)) or len(bounds) != 2
                or not all(isinstance(x, (int, float)) and math.isfinite(x) for x in bounds)
                or bounds[0] > bounds[1]):
            raise ValueError(f"Invalid range for {key}: need [low, high] with low <= high.")
        clean[key] = (float(bounds[0]), float(bounds[1]))

    rng = random.Random(seed)
    samples: dict[str, list[float]] = {m: [] for m in METRICS}
    no_irr = 0
    for _ in range(n):
        trial = dict(deal_inputs)
        for key, (lo, hi) in clean.items():
            trial[key] = rng.uniform(lo, hi)
        derived = underwrite(trial)["derived"]
        for metric in METRICS:
            val = derived.get(metric)
            if isinstance(val, (int, float)) and math.isfinite(val):
                samples[metric].append(float(val))
            elif metric == "irr":
                no_irr += 1

    def summarize(vals: list[float]) -> dict[str, Any]:
        s = sorted(vals)
        return {
            "n": len(s),
            "p10": _percentile(s, 10),
            "p50": _percentile(s, 50),
            "p90": _percentile(s, 90),
            "mean": sum(s) / len(s),
        } if s else {"n": 0}

    irr_vals = samples["irr"]
    coc_vals = samples["cash_on_cash"]
    summary = {
        "n": n,
        "seed": seed,
        "ranges": {k: list(v) for k, v in clean.items()},
        "assumption": "Independent uniform draws per ranged input. Ignores correlations between inputs; understates joint-tail risk.",
        "metrics": {m: summarize(samples[m]) for m in METRICS},
        "p_irr_negative": (sum(1 for v in irr_vals if v < 0) / len(irr_vals)) if irr_vals else None,
        "p_cash_on_cash_negative": (sum(1 for v in coc_vals if v < 0) / len(coc_vals)) if coc_vals else None,
        "frac_irr_uncomputable": no_irr / n,
        "note": "P(loss) uses IRR < 0 among computable draws. Draws where IRR is uncomputable are reported separately, never folded into the probabilities.",
    }
    return summary


def save_simulation(
    conn: sqlite3.Connection, deal_id: str, config: dict[str, Any], summary: dict[str, Any]
) -> dict[str, Any]:
    import json

    ensure_schema(conn)
    created = utc_now()
    cur = conn.execute(
        "INSERT INTO simulations (deal_id, config, summary, created_at) VALUES (?, ?, ?, ?)",
        (deal_id, json.dumps(config), json.dumps(summary), created),
    )
    conn.commit()
    return {"id": cur.lastrowid, "deal_id": deal_id, "config": config,
            "summary": summary, "created_at": created}


def list_simulations(conn: sqlite3.Connection, deal_id: str) -> list[dict[str, Any]]:
    import json

    ensure_schema(conn)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, deal_id, config, summary, created_at FROM simulations"
        " WHERE deal_id = ? ORDER BY created_at, id",
        (deal_id,),
    ).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        rec = dict(row)
        rec["config"] = json.loads(rec["config"])
        rec["summary"] = json.loads(rec["summary"])
        out.append(rec)
    return out
