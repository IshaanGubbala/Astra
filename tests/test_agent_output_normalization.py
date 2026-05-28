from backend.core.agent import Agent


def test_marketing_normalizes_ad_images():
    agent = Agent(name="marketing", role="m", tools={})
    output = {}
    normalized = agent._normalize_done_output(output, [
        ("generate_ad_image", {"image_url": "https://img.example/a.png", "prompt": "ad visual"}),
        ("generate_ad_image", {"base64": "a" * 120, "prompt": "ad visual 2"}),
    ])
    assert "ad_images" in normalized
    assert len(normalized["ad_images"]) == 2


def test_sales_normalizes_leads_sequences_and_contacts():
    agent = Agent(name="sales", role="s", tools={})
    normalized = agent._normalize_done_output({}, [
        ("find_leads", {"leads": [{"company": "Acme"}]}),
        ("build_outreach_sequence", {"lead": {"company": "Acme"}, "sequence": [{"send_day": 1, "subject": "Hi"}]}),
        ("build_crm_contact", {"company": "Acme", "email": "a@acme.com"}),
    ])
    assert normalized["leads"][0]["company"] == "Acme"
    assert normalized["sequence"][0]["subject"] == "Hi"
    assert normalized["crm_contacts"][0]["email"] == "a@acme.com"


def test_design_normalizes_design_spec_wireframes_logo():
    agent = Agent(name="design", role="d", tools={})
    normalized = agent._normalize_done_output({}, [
        ("generate_design_spec", {"product": "Astra"}),
        ("generate_wireframe", {"page_type": "landing"}),
        ("generate_logo_brief", {"direction": "minimal"}),
    ])
    assert normalized["design_spec"]["product"] == "Astra"
    assert normalized["wireframes"][0]["page_type"] == "landing"
    assert normalized["logo_brief"]["direction"] == "minimal"


def test_legal_normalizes_documents_from_tool_sequence():
    agent = Agent(name="legal", role="l", tools={})
    normalized = agent._normalize_done_output({}, [
        ("format_legal_document", {"doc_type": "privacy_policy", "formatted_text": "Policy text"}),
        ("generate_pdf", {"path": "/tmp/privacy_policy.pdf"}),
    ])
    assert normalized["documents"][0]["doc_type"] == "privacy_policy"
    assert normalized["documents"][0]["path"] == "/tmp/privacy_policy.pdf"
