"""Generate a ~200-word company snapshot in markdown from Apify crawl content."""
from __future__ import annotations

from growme.llm_clients import complete
from growme.research.apify_clients import run_website_crawler

SNAPSHOT_SYSTEM = (
    "You are a sales-enablement researcher. Given crawled marketing content, "
    "produce a ~200-word factual company snapshot. Cover: what the company does, "
    "who it sells to (ICP signals), product positioning, and notable proof points. "
    "Use plain prose, no bullets, no marketing fluff."
)


def run(company_url: str) -> str:
    """Returns markdown company snapshot. Hits Apify website-content-crawler live."""
    pages = run_website_crawler([_https(company_url)], max_pages=3)
    blob = "\n\n".join(_extract_text(p) for p in pages if _extract_text(p))[:12_000]
    return complete(
        role="research_synth",
        system=SNAPSHOT_SYSTEM,
        user=f"Crawled content from {company_url}:\n\n{blob}",
        max_tokens=600,
    ).strip()


def _https(url: str) -> str:
    return url if url.startswith("http") else f"https://{url}"


def _extract_text(page: dict) -> str:
    return page.get("text") or page.get("markdown") or ""


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    print(run("neon.tech"))
