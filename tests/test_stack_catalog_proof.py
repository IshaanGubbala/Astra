from backend.stack_catalog_proof import build_stack_catalog_proof
from backend.stacks.templates import PROMISED_AGENT_STACK_IDS


def test_stack_catalog_proof_compiles_every_promised_stack():
    proof = build_stack_catalog_proof()

    assert proof["ok"] is True
    assert proof["stack_count"] == len(PROMISED_AGENT_STACK_IDS)
    assert proof["ready_count"] == len(PROMISED_AGENT_STACK_IDS)
    assert proof["failed"] == []

    for stack in proof["stacks"]:
        assert stack["ok"] is True
        assert stack["quality_score"] == 100
        assert stack["lane_count"] == stack["task_count"]
        assert stack["artifact_acceptance_count"] == stack["artifact_count"]
        assert stack["connector_count"] > 0
        assert stack["approval_count"] > 0
        assert stack["milestone_count"] >= 3
        assert stack["kpi_count"] >= 3
        assert stack["quality_gate_count"] >= 3


def test_stack_catalog_proof_is_available_from_admin_endpoint():
    from backend.api.admin import stack_catalog_proof

    assert callable(stack_catalog_proof)
