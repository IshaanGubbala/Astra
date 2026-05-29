from backend.stacks import PROMISED_AGENT_STACK_IDS, audit_stack_template, get_stack_template, recommend_stack
from backend.stacks.templates import STACK_TEMPLATES


def test_catalog_contains_promised_agent_stack_platform_segments():
    """Lock the business promise: outcome -> deployable AI department."""
    assert set(PROMISED_AGENT_STACK_IDS) == {
        "idea_to_revenue",
        "sales",
        "marketing",
        "founder_ops",
        "support",
        "product",
    }
    assert set(PROMISED_AGENT_STACK_IDS).issubset(STACK_TEMPLATES)

    for stack_id in PROMISED_AGENT_STACK_IDS:
        stack = get_stack_template(stack_id)
        audit = audit_stack_template(stack)

        assert audit["ready"] is True, (stack_id, audit["gaps"])
        assert stack.tasks
        assert stack.artifacts
        assert stack.approval_gates
        assert stack.connector_requirements
        assert stack.dashboard_sections
        assert stack.completion_rules
        assert all(task.artifacts for task in stack.tasks)


def test_stack_compiler_routes_business_outcomes_to_promised_stacks():
    examples = {
        "idea_to_revenue": "I have a startup idea and need ICP, competitor research, pricing, a landing page, and an investor plan.",
        "sales": "Build a sales pipeline with CRM stages, prospects, outbound sequences, and follow up.",
        "marketing": "Launch a growth campaign with content, paid ads, social creative, and measurement.",
        "founder_ops": "Create a weekly operating cadence, decision log, metrics, investor update, and answer what engineering did.",
        "support": "Triage customer support tickets, build macros, define SLA escalation, and create a knowledge base.",
        "product": "Plan a product roadmap, user stories, requirements, technical spec, and release scope.",
    }

    for expected_stack_id, goal in examples.items():
        recommendation = recommend_stack(goal, company_stage="existing business" if expected_stack_id != "idea_to_revenue" else "idea")

        assert recommendation.stack.stack_id == expected_stack_id
        assert recommendation.confidence >= 0.6
        assert recommendation.matched_signals
