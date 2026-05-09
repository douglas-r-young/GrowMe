"""Extract customer voice (use cases + friction phrases) from G2 reviews."""
from __future__ import annotations

import json

from growme.llm_clients import complete_json
from growme.research.apify_clients import run_g2_scraper
from growme.research.citation import cited_fact, source_g2
from growme.schemas import CitedFact
from pydantic import BaseModel, Field


class _Voice(BaseModel):
    use_cases: list[str] = Field(default_factory=list, max_length=5)
    friction_phrases: list[str] = Field(default_factory=list, max_length=5)


VOICE_SYSTEM = (
    "You are a sales-enablement researcher. Given a list of G2 reviews, extract:\n"
    " - use_cases: 3-5 concise verbs/phrases describing what customers actually do with the product\n"
    " - friction_phrases: 3-5 verbatim or near-verbatim phrases describing friction "
    "(slow, hard, broken, etc.)\n"
    "Avoid marketing language. Stay close to the source phrasing."
)


def run(g2_product_url: str) -> list[CitedFact]:
    """Returns CitedFacts: 3-5 'use_case: X' + 3-5 'friction: X' entries."""
    reviews = run_g2_scraper(g2_product_url, max_reviews=25)
    review_blob = json.dumps(
        [{"title": r.get("title"), "text": r.get("review_text") or r.get("review") or ""}
         for r in reviews][:25],
        indent=2,
    )[:12_000]

    voice = complete_json(
        role="research_extract",
        system=VOICE_SYSTEM,
        user=f"Reviews:\n{review_blob}",
        schema=_Voice,
    )

    out: list[CitedFact] = []
    for uc in voice.use_cases:
        out.append(cited_fact(f"use_case: {uc}", source_g2(g2_product_url), "high"))
    for fp in voice.friction_phrases:
        out.append(cited_fact(f"friction: {fp}", source_g2(g2_product_url), "high"))
    return out


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    facts = run("https://www.g2.com/products/neon/reviews")
    for f in facts:
        print(f.confidence, "-", f.text)
