"""Persistent active research task storage."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict

from .research_tasks import ResearchTask
from .state import now_iso


class ResearchTaskStore:
    def __init__(self, path: str = "data/growth.db") -> None:
        self.path = path
        with sqlite3.connect(self.path) as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS research_tasks (
                    prospect_id TEXT PRIMARY KEY,
                    task_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            db.commit()

    def set(self, task: ResearchTask) -> ResearchTask:
        timestamp = now_iso()
        encoded = json.dumps(asdict(task), sort_keys=True)
        with sqlite3.connect(self.path) as db:
            db.execute(
                """
                INSERT INTO research_tasks
                (prospect_id, task_json, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(prospect_id) DO UPDATE SET
                    task_json = excluded.task_json,
                    updated_at = excluded.updated_at
                """,
                (task.prospect_id, encoded, timestamp, timestamp),
            )
            db.commit()
        return task

    def get(self, prospect_id: str) -> ResearchTask | None:
        with sqlite3.connect(self.path) as db:
            row = db.execute(
                "SELECT task_json FROM research_tasks WHERE prospect_id = ?",
                (prospect_id,),
            ).fetchone()
        if row is None:
            return None
        data = json.loads(row[0])
        return ResearchTask(**data)

    def clear(self, prospect_id: str) -> None:
        with sqlite3.connect(self.path) as db:
            db.execute(
                "DELETE FROM research_tasks WHERE prospect_id = ?",
                (prospect_id,),
            )
            db.commit()
