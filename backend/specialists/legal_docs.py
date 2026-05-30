"""Legal docs specialist — drafts privacy policy, ToS, NDA, and IP assignment agreements as PDFs."""
from backend.core.agent import Agent
from backend.tools.obsidian_logger import obsidian_log, obsidian_read, obsidian_append
from backend.tools.doc_generator import format_legal_document
from backend.tools.pdf_generator import generate_pdf


def build_legal_docs_agent(**kwargs) -> Agent:
    _obsidian_read_done = {"done": False}

    def _obsidian_read_once(**kw):
        if _obsidian_read_done["done"]:
            return {"notes": [], "_blocked": "obsidian_read already called — proceed to format_legal_document NOW"}
        _obsidian_read_done["done"] = True
        return obsidian_read(**kw)

    return Agent(
        name="legal_docs",
        role=(
            "You are a legal documents specialist. Draft full legal documents and save each as a PDF.\n\n"
            "MANDATORY WORKFLOW — execute every step in order:\n"
            "1. obsidian_read(agent='research', founder_id=<FOUNDER_ID>) — get company name, business model, data handling details. "
            "If no notes found, use the goal/shared context and proceed immediately — do NOT retry.\n"
            "2. format_legal_document(doc_type='privacy_policy', company_name=<COMPANY_NAME from SHARED CONTEXT>, content=<full detailed privacy policy text>)\n"
            "   IMMEDIATELY after: generate_pdf(content=<formatted_text from step 2>, filename='privacy_policy.pdf')\n"
            "3. format_legal_document(doc_type='terms_of_service', company_name=<COMPANY_NAME>, content=<full terms of service text>)\n"
            "   IMMEDIATELY after: generate_pdf(content=<formatted_text from step 3>, filename='terms_of_service.pdf')\n"
            "4. format_legal_document(doc_type='nda', company_name=<COMPANY_NAME>, content=<full mutual NDA text including definitions, obligations, exclusions, term, remedies>)\n"
            "   IMMEDIATELY after: generate_pdf(content=<formatted_text from step 4>, filename='nda.pdf')\n"
            "5. format_legal_document(doc_type='ip_assignment', company_name=<COMPANY_NAME>, content=<full IP assignment agreement text including assignment of inventions, work-for-hire, moral rights waiver, representations>)\n"
            "   IMMEDIATELY after: generate_pdf(content=<formatted_text from step 5>, filename='ip_assignment.pdf')\n"
            "6. obsidian_log — log all document titles and PDF file paths\n"
            "7. done — return {documents: [{doc_type, title, path, text}]}\n\n"
            "RULES: NEVER skip generate_pdf. Call it immediately after EACH format_legal_document. "
            "Use COMPANY_NAME from SHARED CONTEXT as the company name everywhere. "
            "Write FULL document content — not placeholders or stubs. "
            "done output MUST include a documents array where each entry has path (the PDF filepath returned by generate_pdf)."
        ),
        tools={
            "format_legal_document": format_legal_document,
            "generate_pdf": generate_pdf,
            "obsidian_log": obsidian_log,
            "obsidian_read": _obsidian_read_once,
            "obsidian_append": obsidian_append,
        },
        **kwargs,
    )
