from backend.stacks import build_goal_stack_package


def test_goal_stack_package_compiles_business_outcome_into_department_contract(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    package = build_goal_stack_package(
        instruction="I have a startup idea and need ICP, pricing, competitor research, a landing page, and investor materials.",
        founder_id="founder_pkg",
        company_stage="idea",
        company_name="Astra",
    )

    assert package["ok"] is True
    assert package["stack_id"] == "idea_to_revenue"
    assert package["recommendation"]["stack"]["stack_id"] == "idea_to_revenue"
    assert package["manifest"]["department_name"] == "Idea to Revenue Stack Department"
    assert package["execution_blueprint"]["execution_mode"] == "agent_department"
    assert package["operating_plan"]["execution_blueprint"]["stack_id"] == "idea_to_revenue"
    assert package["connector_setup"]["required"]
    assert package["approval_queue"]
    assert package["start_payload"]["stack_id"] == "idea_to_revenue"
    assert package["start_payload"]["constraints"]["stack_id"] == "idea_to_revenue"
    assert package["proof"]["has_manifest"] is True
    assert package["proof"]["has_execution_blueprint"] is True
    assert package["proof"]["has_connector_plan"] is True
    assert package["proof"]["has_approval_policy"] is True
    assert package["proof"]["has_artifact_contract"] is True
    assert package["proof"]["has_memory_policy"] is True
    assert package["proof"]["has_human_collaboration_model"] is True


def test_goal_stack_package_routes_existing_business_sales_stack(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    package = build_goal_stack_package(
        instruction="Build a sales pipeline with CRM stages, lead sourcing, outbound emails, and weekly follow up.",
        founder_id="founder_pkg",
        company_stage="existing business",
    )

    assert package["stack_id"] == "sales"
    assert package["manifest"]["workflow"]["nodes"]
    assert "sales" in package["summary"].lower()
