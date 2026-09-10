from app.cre_workflow import CREWorkflowStage, next_stage


def test_cre_workflow_is_explicit_and_ordered():
    assert next_stage(CREWorkflowStage.OPPORTUNITY) is CREWorkflowStage.SCREENING
    assert next_stage(CREWorkflowStage.UNDERWRITING) is CREWorkflowStage.DUE_DILIGENCE
    assert next_stage(CREWorkflowStage.OBSERVE_OUTCOME) is CREWorkflowStage.EPISTEMIC_MEMORY
    assert next_stage(CREWorkflowStage.EPISTEMIC_MEMORY) is None
