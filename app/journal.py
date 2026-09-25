"""Decision journal and Observer.

Implements the tail of Charter §20's institutional learning loop:

  DECISION -> OUTCOME -> OBSERVATION -> LESSON -> PERSISTENT MEMORY

When a deal moves to PURSUE, the human may record a thesis: what they
believe, the key assumptions it rests on, and the expected outcome. Later,
an outcome (what actually happened) and a lesson can be recorded. The
Observer endpoint compares theses against outcomes side by side and lists
lessons learned. It does not score, grade, or rewrite history: a thesis is
immutable once recorded, and an outcome never edits the thesis it follows.

Human authority (Charter §5) is preserved throughout: the journal records
human decisions; it never makes them.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

from app.deal_flow import get_deal


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS theses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id TEXT NOT NULL,
            thesis TEXT NOT NULL,
            key_assumptions TEXT NOT NULL,
            expected_outcome TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id TEXT NOT NULL,
            actual_outcome TEXT NOT NULL,
            lesson TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_theses_deal ON theses(deal_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_deal ON outcomes(deal_id)")


def record_thesis(
    conn: sqlite3.Connection,
    deal_id: str,
    thesis: str,
    key_assumptions: list[str] | None = None,
    expected_outcome: str | None = None,
) -> dict[str, Any]:
    """Record a decision thesis. Only allowed while the deal is PURSUE."""
    import json

    deal = get_deal(deal_id)
    if not deal:
        raise KeyError(f"Deal {deal_id} not found.")
    if deal.get("status") != "PURSUE":
        raise ValueError(
            f"Thesis can only be recorded for a PURSUE deal; {deal_id} is {deal.get('status')}."
        )
    if not thesis or not str(thesis).strip():
        raise ValueError("Thesis must not be empty.")
    ensure_schema(conn)
    created = utc_now()
    assumptions = list(key_assumptions or [])
    cur = conn.execute(
        "INSERT INTO theses (deal_id, thesis, key_assumptions, expected_outcome, created_at)"
        " VALUES (?, ?, ?, ?, ?)",
        (deal_id, thesis, json.dumps(assumptions), expected_outcome, created),
    )
    conn.commit()
    return {
        "id": cur.lastrowid,
        "deal_id": deal_id,
        "thesis": thesis,
        "key_assumptions": assumptions,
        "expected_outcome": expected_outcome,
        "created_at": created,
    }


def record_outcome(
    conn: sqlite3.Connection,
    deal_id: str,
    actual_outcome: str,
    lesson: str | None = None,
) -> dict[str, Any]:
    if not actual_outcome or not str(actual_outcome).strip():
        raise ValueError("Actual outcome must not be empty.")
    ensure_schema(conn)
    created = utc_now()
    cur = conn.execute(
        "INSERT INTO outcomes (deal_id, actual_outcome, lesson, created_at)"
        " VALUES (?, ?, ?, ?)",
        (deal_id, actual_outcome, lesson, created),
    )
    conn.commit()
    return {
        "id": cur.lastrowid,
        "deal_id": deal_id,
        "actual_outcome": actual_outcome,
        "lesson": lesson,
        "created_at": created,
    }


def _all(conn: sqlite3.Connection, table: str, deal_id: str | None = None) -> list[dict[str, Any]]:
    import json

    ensure_schema(conn)
    conn.row_factory = sqlite3.Row
    if deal_id:
        rows = conn.execute(
            f"SELECT * FROM {table} WHERE deal_id = ? ORDER BY created_at, id", (deal_id,)
        ).fetchall()
    else:
        rows = conn.execute(f"SELECT * FROM {table} ORDER BY created_at, id").fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        rec = dict(row)
        if "key_assumptions" in rec and isinstance(rec["key_assumptions"], str):
            rec["key_assumptions"] = json.loads(rec["key_assumptions"])
        out.append(rec)
    return out


def list_theses(conn: sqlite3.Connection, deal_id: str) -> list[dict[str, Any]]:
    return _all(conn, "theses", deal_id)


def list_outcomes(conn: sqlite3.Connection, deal_id: str) -> list[dict[str, Any]]:
    return _all(conn, "outcomes", deal_id)


def observer_summary(conn: sqlite3.Connection) -> dict[str, Any]:
    """Compare theses vs outcomes across deals; list lessons learned.

    Presents each deal's thesis alongside its outcome without scoring.
    Lessons are collected verbatim.
    """
    ensure_schema(conn)
    theses = _all(conn, "theses")
    outcomes = _all(conn, "outcomes")
    by_deal: dict[str, dict[str, Any]] = {}
    for t in theses:
        entry = by_deal.setdefault(t["deal_id"], {"deal_id": t["deal_id"], "theses": [], "outcomes": []})
        entry["theses"].append(t)
    for o in outcomes:
        entry = by_deal.setdefault(o["deal_id"], {"deal_id": o["deal_id"], "theses": [], "outcomes": []})
        entry["outcomes"].append(o)

    deals: list[dict[str, Any]] = []
    lessons: list[dict[str, Any]] = []
    for deal_id, entry in sorted(by_deal.items()):
        deal = get_deal(deal_id) or {}
        inputs = deal.get("original_inputs", {}) if isinstance(deal, dict) else {}
        latest_thesis = entry["theses"][-1] if entry["theses"] else None
        latest_outcome = entry["outcomes"][-1] if entry["outcomes"] else None
        deals.append({
            "deal_id": deal_id,
            "name": inputs.get("name"),
            "status": deal.get("status") if isinstance(deal, dict) else None,
            "thesis": latest_thesis,
            "outcome": latest_outcome,
            "thesis_count": len(entry["theses"]),
            "outcome_count": len(entry["outcomes"]),
        })
        for o in entry["outcomes"]:
            if o.get("lesson"):
                lessons.append({"deal_id": deal_id, "lesson": o["lesson"], "created_at": o["created_at"]})

    n_theses = len(theses)
    n_outcomes = len(outcomes)
    return {
        "counts": {
            "theses_recorded": n_theses,
            "outcomes_recorded": n_outcomes,
            "lessons_recorded": len(lessons),
            "theses_awaiting_outcome": sum(1 for d in deals if d["thesis"] and not d["outcome"]),
        },
        "deals": deals,
        "lessons": lessons,
        "note": "Theses and outcomes are shown side by side, unedited. The Observer does not score decisions; it preserves the record so judgment can compound.",
    }
