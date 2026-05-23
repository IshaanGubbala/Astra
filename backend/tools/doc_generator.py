from datetime import date

DISCLAIMER = (
    "AI-generated document preparation — not legal advice. "
    "Review with a licensed attorney before signing."
)

DOC_TYPE_LABELS = {
    "founder_agreement": "Founder Agreement",
    "nda": "Non-Disclosure Agreement",
    "ip_assignment": "IP Assignment Agreement",
    "vesting_schedule": "Vesting Schedule",
}


def format_legal_document(doc_type: str, company_name: str, content: str) -> str:
    label = DOC_TYPE_LABELS.get(doc_type, doc_type.replace("_", " ").title())
    today = date.today().isoformat()
    return f"""================================================================================
{label.upper()}
Company: {company_name}
Date: {today}
================================================================================

{content}

================================================================================
DISCLAIMER: {DISCLAIMER}
================================================================================
"""
