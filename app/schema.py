"""Additive schema migration for Charter-aligned tables.

Creates every new table with CREATE TABLE IF NOT EXISTS: existing tables
(and the deals inside them) are never altered, dropped, or rewritten.
Safe to run on every startup.
"""

from __future__ import annotations

from app import evidence, journal, perspectives, scenarios, simulation
from app.deal_flow import connect


def migrate() -> None:
    conn = connect()
    try:
        for module in (evidence, perspectives, scenarios, simulation, journal):
            module.ensure_schema(conn)
        conn.commit()
    finally:
        conn.close()
