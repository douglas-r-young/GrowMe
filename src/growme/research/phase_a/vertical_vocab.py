# src/growme/research/phase_a/vertical_vocab.py
"""Pull 10-15 domain vocabulary terms from a company's marketing content."""
from __future__ import annotations

from pydantic import BaseModel, Field

from growme.llm_clients import complete_json
from growme.research.apify_clients import run_website_crawler


class _Vocab(BaseModel):
    terms: list[str] = Field(default_factory=list, min_length=10, max_length=15)


VOCAB_SYSTEM = (
    "You extract domain-specific vocabulary. Given crawled marketing content, "
    "return 10-15 short technical terms or product nouns specific to this company's "
    "vertical. Avoid generic SaaS terms (e.g., 'SaaS', 'platform'). Single words or short phrases. "
    "Return strictly as JSON object with a 'terms' array."
)


def run(company_url: str) -> list[str]:
    pages = run_website_crawler([_https(company_url)], max_pages=4)
    blob = "\n\n".join(_extract_text(p) for p in pages)[:10_000]
    vocab = complete_json(
        role="research_extract",
        system=VOCAB_SYSTEM,
        user=f"Content:\n{blob}",
        schema=_Vocab,
    )
    return vocab.terms


def _https(url: str) -> str:
    return url if url.startswith("http") else f"https://{url}"


def _extract_text(page: dict) -> str:
    return page.get("text") or page.get("markdown") or ""


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    print(run("neon.tech"))
