"""
Real parts lookup — enriches BOM items with purchase links via web search.
"""
import logging
import time

logger = logging.getLogger(__name__)

_SEARCH_AVAILABLE = False
try:
    from duckduckgo_search import DDGS
    _SEARCH_AVAILABLE = True
except ImportError:
    pass


def enrich_bom_with_links(bom_items: list) -> list:
    """Add purchase links to BOM items via DuckDuckGo search."""
    if not _SEARCH_AVAILABLE:
        logger.warning("duckduckgo_search not installed — skipping parts enrichment")
        return bom_items

    enriched = []
    for item in bom_items:
        component = item.get("component", "")
        part_number = item.get("part_number", "")
        query = f"buy {part_number or component} electronics"

        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
            links = []
            for r in results:
                url = r.get("href", "")
                title = r.get("title", "")
                # Filter to known retailers
                if any(shop in url for shop in [
                    "amazon.com", "aliexpress.com", "mouser.com",
                    "digikey.com", "adafruit.com", "sparkfun.com",
                    "ebay.com", "lcsc.com", "robotshop.com"
                ]):
                    links.append({"retailer": title[:60], "url": url})
            item = {**item, "purchase_links": links[:3]}
            time.sleep(0.3)  # rate limit
        except Exception as e:
            logger.warning("Parts lookup failed for %s: %s", component, e)
            item = {**item, "purchase_links": []}

        enriched.append(item)

    return enriched


def get_datasheet_link(component: str, part_number: str) -> str | None:
    """Search for component datasheet."""
    if not _SEARCH_AVAILABLE:
        return None
    query = f"{part_number or component} datasheet filetype:pdf"
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        for r in results:
            url = r.get("href", "")
            if ".pdf" in url.lower() or "datasheet" in url.lower():
                return url
    except Exception as e:
        logger.warning("Datasheet lookup failed: %s", e)
    return None
