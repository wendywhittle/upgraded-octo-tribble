"""Research task contract for controlled external research adapters."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResearchTask:
    prospect_id: str
    target: str
    query: str
    purpose: str


def build_research_task(
    prospect_id: str,
    target: str,
    query: str,
    purpose: str,
) -> ResearchTask:
    values = {
        "prospect_id": prospect_id,
        "target": target,
        "query": query,
        "purpose": purpose,
    }
    for name, value in values.items():
        if not value or not value.strip():
            raise ValueError(f"{name} is required")

    return ResearchTask(
        prospect_id=prospect_id.strip(),
        target=target.strip(),
        query=query.strip(),
        purpose=purpose.strip(),
    )
