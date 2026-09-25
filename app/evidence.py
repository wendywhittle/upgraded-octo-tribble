"""Per-deal evidence log.

Implements the Charter's evidence requirements (§2.2 Evidence Before
Assertion, §13 Provenance): every material claim attached to a deal is
recorded with its epistemic type, its source, and a timestamp. The type
ladder is fixed so downstream analysis (perspectives, observer) can weigh
evidence honestly instead of treating all claims alike.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

EVIDENCE_TYPES = ("observed", "sourced", "calculated", "assumed", "hypothesis")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id TEXT NOT NULL,
            type TEXT NOT NULL,
            source TEXT,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_evidence_deal ON evidence(deal_id)")


def add_evidence(
    conn: sqlite3.Connection,
    deal_id: str,
    evidence_type: str,
    content: str,
    source: str | None = None,
) -> dict[str, Any]:
    if evidence_type not in EVIDENCE_TYPES:
        raise ValueError(
            f"Invalid evidence type {evidence_type!r}; must be one of {EVIDENCE_TYPES}."
        )
    if not content or not str(content).strip():
        raise ValueError("Evidence content must not be empty.")
    ensure_schema(conn)
    created = utc_now()
    cur = conn.execute(
        "INSERT INTO evidence (deal_id, type, source, content, created_at)"
        " VALUES (?, ?, ?, ?, ?)",
        (deal_id, evidence_type, source, content, created),
    )
    conn.commit()
    return {
        "id": cur.lastrowid,
        "deal_id": deal_id,
        "type": evidence_type,
        "source": source,
        "content": content,
        "created_at": created,
    }


def list_evidence(conn: sqlite3.Connection, deal_id: str) -> list[dict[str, Any]]:
    ensure_schema(conn)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, deal_id, type, source, content, created_at"
        " FROM evidence WHERE deal_id = ? ORDER BY created_at, id",
        (deal_id,),
    ).fetchall()
    return [dict(row) for row in rows]
