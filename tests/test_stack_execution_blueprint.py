from backend.stacks import (
    audit_stack_template,
    build_stack_execution_blueprint,
    build_stack_manifest,
    build_stack_operating_plan,
    get_stack_template,
)
from backend.stacks.templates import STACK_TEMPLATES


def test_execution_blueprint_expands_every_template_into_lane_work_packets():
    for stack_id, stack in STACK_TEMPLATES.items():
        blueprint = build_stack_execution_blueprint(stack, "Launch a useful business operating system", "Astra")

        assert blueprint["stack_id"] == stack_id
        assert blueprint["execution_mode"] == "agent_department"
        assert len(blueprint["lanes"]) == len(stack.tasks)
        assert blueprint["calendar"]
        assert blueprint["completion_audit"]
        assert blueprint["operating_controls"]["approvals"]

        lane_by_id = {lane["id"]: lane for lane in blueprint["lanes"]}
        for task in stack.tasks:
            lane = lane_by_id[task.id]
            assert len(lane["steps"]) >= 4
            assert lane["status_model"] == ["waiting", "running", "blocked", "ready_for_review", "done"]
            assert lane["handoff_packet"]["must_include"]
            assert {item["artifact_key"] for item in lane["deliverables"]} == set(task.artifacts)
            for deliverable in lane["deliverables"]:
                assert len(deliverable["acceptance_checks"]) >= 4
                assert any("Company Brain" in check for check in deliverable["acceptance_checks"])


def test_execution_blueprint_maps_required_connectors_and_approval_gates():
    stack = get_stack_template("idea_to_revenue")
    blueprint = build_stack_execution_blueprint(stack, "Build a waitlist SaaS for creators")

    connector_by_key = {connector["key"]: connector for connector in blueprint["connector_dependencies"]}
    assert connector_by_key["github"]["required"] is True
    assert connector_by_key["vercel"]["required"] is True
    assert connector_by_key["github"]["used_by_lanes"]
    assert connector_by_key["vercel"]["blocking_rule"] == "Required for hands-off execution"

    approval_by_key = {approval["key"]: approval for approval in blueprint["approvals"]}
    assert approval_by_key["public_deploy"]["watch_lanes"]
    assert approval_by_key["outbound_send"]["watch_lanes"]
    assert approval_by_key["legal_publish"]["watch_lanes"]


def test_operating_plan_and_manifest_include_execution_blueprint():
    stack = get_stack_template("sales")
    operating_plan = build_stack_operating_plan(stack, "Build a B2B sales machine", "Astra")
    manifest = build_stack_manifest(stack, "Build a B2B sales machine", "Astra")

    assert operating_plan["execution_blueprint"]["stack_id"] == "sales"
    assert operating_plan["execution_blueprint"]["artifact_acceptance_matrix"]
    assert manifest["operating_plan"]["execution_blueprint"]["stack_id"] == "sales"
    assert manifest["workflow"]["nodes"]
    assert manifest["template_quality"]["ready"] is True


def test_every_stack_template_passes_production_depth_audit():
    for stack_id, stack in STACK_TEMPLATES.items():
        audit = audit_stack_template(stack)

        assert audit["ready"] is True, (stack_id, audit["gaps"])
        assert audit["score"] == 100
        assert any(check["key"] == "minimum_lanes" for check in audit["checks"])
        assert any(check["key"] == "required_connector" for check in audit["checks"])
        assert any(check["key"] == "handoff_terminal_lane" for check in audit["checks"])
