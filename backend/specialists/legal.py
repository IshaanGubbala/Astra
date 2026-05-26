"""Legal specialist — generates NDAs, privacy policies, terms, patent landscape."""
from backend.core.agent import Agent
from backend.tools.obsidian_logger import obsidian_log, obsidian_read, obsidian_append
from backend.tools.pdf_generator import generate_pdf
from backend.tools.patent_search import patent_search
from backend.tools.doc_generator import format_legal_document


def build_legal_agent(**kwargs) -> Agent:
    return Agent(
        name="legal",
        role=(
            "You are a legal specialist. Draft legal documents and save them as PDFs. "
            "format_legal_document formats a document given doc_type, company_name, and content (describe the product, "
            "data collected, users served, jurisdiction). generate_pdf saves it to disk. "
            "patent_search surveys the IP landscape. "
            "Always generate at least one document. Call obsidian_log then done."
        ),
        tools={
            "generate_pdf": generate_pdf,
            "patent_search": patent_search,
            "format_legal_document": format_legal_document,
            "obsidian_log": obsidian_log,
            "obsidian_read": obsidian_read,
            "obsidian_append": obsidian_append,
        },
        **kwargs,
    )
