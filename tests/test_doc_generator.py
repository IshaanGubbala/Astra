from backend.tools.doc_generator import format_legal_document, DISCLAIMER


def test_format_adds_disclaimer():
    doc = format_legal_document(
        doc_type="founder_agreement",
        company_name="AcmeCo",
        content="This is the agreement body.",
    )
    assert DISCLAIMER in doc


def test_format_includes_company_name():
    doc = format_legal_document(
        doc_type="founder_agreement",
        company_name="AcmeCo",
        content="Agreement body here.",
    )
    assert "AcmeCo" in doc


def test_format_includes_content():
    content = "Section 1: Equity split is 50/50."
    doc = format_legal_document(
        doc_type="nda",
        company_name="AcmeCo",
        content=content,
    )
    assert content in doc
