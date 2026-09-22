"""Select the next research task from explicit evidence gaps."""

from __future__ import annotations

from growth.qualification import SignalCategory
from growth.research_tasks import ResearchTask


def next_research_task(
    prospect_id: str,
    known: set[SignalCategory],
) -> ResearchTask | None:
    if SignalCategory.ACQUISITION_APPETITE not in known:
        return ResearchTask(
            prospect_id,
            "current acquisition strategy",
            "current acquisition criteria and investment strategy",
            "Establish whether the prospect is actively acquiring",
        )

    if not (
        {
            SignalCategory.ASSET_FIT,
            SignalCategory.GEOGRAPHIC_FIT,
            SignalCategory.DEAL_SIZE_FIT,
        }
        & known
    ):
        return ResearchTask(
            prospect_id,
            "investment criteria",
            "asset type geography and acquisition size criteria",
            "Establish at least one concrete fit dimension",
        )

    if SignalCategory.DECISION_MAKER not in known:
        return ResearchTask(
            prospect_id,
            "acquisitions contact",
            "current acquisitions team and public business-development contact",
            "Identify an appropriate human contact without initiating outreach",
        )

    return None
