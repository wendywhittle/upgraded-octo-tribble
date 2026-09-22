"""Deterministic persistent prospect state for the Growth Engine experiment."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import sqlite3
from typing import Any


STATES = (
    "DISCOVER",
    "RESEARCH",
    "QUALIFY",
    "CONTACT",
    "OUTREACH",
    "WAIT",
    "RESPOND",
    "FOLLOW_UP",
    "CONVERTED",
    "STOPPED",
)

TRANSITIONS = {
    "DISCOVER": {"RESEARCH", "STOPPED"},
    "RESEARCH": {"QUALIFY", "STOPPED"},
    "QUALIFY": {"CONTACT", "STOPPED"},
    "CONTACT": {"OUTREACH", "STOPPED"},
    "OUTREACH": {"WAIT", "STOPPED"},
    "WAIT": {"RESPOND", "STOPPED"},
    "RESPOND": {"FOLLOW_UP", "CONVERTED", "STOPPED"},
    "FOLLOW_UP": {"WAIT", "CONVERTED", "STOPPED"},
    "CONVERTED": set(),
    "STOPPED": set(),
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Prospect:
    prospect_id: str
    account: str
    current_state: str
    next_action: str
    created_at: str
    updated_at: str


class GrowthStore:
    """Small SQLite store with explicit state transitions."""

    def __init__(self, path: str = "data/growth.db") -> None:
        self.path = path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS prospects (
                    prospect_id TEXT PRIMARY KEY,
                    account TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    current_state TEXT NOT NULL,
                    next_action TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            db.commit()

    def create(
        self,
        prospect_id: str,
        account: str,
        payload: dict[str, Any],
        next_action: str,
    ) -> Prospect:
        import json

        timestamp = now_iso()
        with self._connect() as db:
            db.execute(
                """
                INSERT INTO prospects
                (prospect_id, account, payload, current_state, next_action, created_at, updated_at)
                VALUES (?, ?, ?, 'DISCOVER', ?, ?, ?)
                """,
                (
                    prospect_id,
                    account,
                    json.dumps(payload, sort_keys=True),
                    next_action,
                    timestamp,
                    timestamp,
                ),
            )
            db.commit()
        return Prospect(prospect_id, account, "DISCOVER", next_action, timestamp, timestamp)

    def transition(self, prospect_id: str, new_state: str, next_action: str) -> Prospect:
        if new_state not in STATES:
            raise ValueError(f"Unknown state: {new_state}")

        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM prospects WHERE prospect_id = ?", (prospect_id,)
            ).fetchone()
            if row is None:
                raise KeyError(prospect_id)

            allowed = TRANSITIONS[row["current_state"]]
            if new_state not in allowed:
                raise ValueError(
                    f"Invalid transition: {row['current_state']} -> {new_state}"
                )

            timestamp = now_iso()
            db.execute(
                """
                UPDATE prospects
                SET current_state = ?, next_action = ?, updated_at = ?
                WHERE prospect_id = ?
                """,
                (new_state, next_action, timestamp, prospect_id),
            )
            db.commit()

            return Prospect(
                prospect_id,
                row["account"],
                new_state,
                next_action,
                row["created_at"],
                timestamp,
            )

    def set_next_action(self, prospect_id: str, next_action: str) -> Prospect:
        """Update the durable next action without changing lifecycle state."""
        if not next_action.strip():
            raise ValueError("next_action must not be blank")

        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM prospects WHERE prospect_id = ?", (prospect_id,)
            ).fetchone()
            if row is None:
                raise KeyError(prospect_id)

            timestamp = now_iso()
            db.execute(
                """
                UPDATE prospects
                SET next_action = ?, updated_at = ?
                WHERE prospect_id = ?
                """,
                (next_action, timestamp, prospect_id),
            )
            db.commit()

            return Prospect(
                prospect_id,
                row["account"],
                row["current_state"],
                next_action,
                row["created_at"],
                timestamp,
            )

    def get(self, prospect_id: str) -> Prospect | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM prospects WHERE prospect_id = ?", (prospect_id,)
            ).fetchone()
        if row is None:
            return None
        return Prospect(
            row["prospect_id"],
            row["account"],
            row["current_state"],
            row["next_action"],
            row["created_at"],
            row["updated_at"],
        )
