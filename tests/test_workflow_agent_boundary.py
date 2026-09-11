import pytest

from app.workflow import ActorType, Opportunity, WorkflowError, WorkflowService, WorkflowState, WorkflowStore


def test_agent_cannot_mutate_workflow_state(tmp_path):
    svc = WorkflowService(WorkflowStore(tmp_path / "workflow.jsonl"))
    deal = svc.create_deal(Opportunity(name="Agent boundary test"))
    with pytest.raises(WorkflowError, match="Agents may reason"):
        svc.transition(deal.deal_id, WorkflowState.SCREENED, "agent-1", ActorType.AGENT, "screened")
