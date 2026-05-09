# src/growme/research/phase_a/named_competitors.py
"""Identify 2-3 named competitors for the company via web search + LLM."""
from __future__ import annotations

from pydantic import BaseModel, Field

from growme.llm_clients import complete_json
from growme.research.citation import cited_fact, source_web
from growme.research.web_search import search
from growme.schemas import CitedFact


class _Competitor(BaseModel):
    name: str
    one_liner: str
    source_url: str = ""


class _Competitors(BaseModel):
    competitors: list[_Competitor] = Field(default_factory=list, min_length=2, max_length=3)


COMPETITORS_SYSTEM = (
    "You are a sales-enablement researcher. Given web search results about a company, "
    "identify 2-3 named competitors that prospects most often evaluate against. "
    "For each: a 1-line positioning of the competitor and a source_url that supports the claim."
)


def run(company_alias: str, company_url: str) -> list[CitedFact]:
    """Returns CitedFacts of competitor positioning."""
    hits = search(f"{company_alias} competitors compare", max_results=6)
    blob = "\n".join(f"- [{h.title}]({h.url}): {h.content}" for h in hits)
    parsed = complete_json(
        role="research_synth",
        system=COMPETITORS_SYSTEM,
        user=(
            f"Company: {company_alias} ({company_url})\n\n"
            f"Web search results:\n{blob}"
        ),
        schema=_Competitors,
    )
    out: list[CitedFact] = []
    for c in parsed.competitors:
        text = f"{c.name}: {c.one_liner}"
        src = source_web(c.source_url) if c.source_url else "inference:web_search"
        out.append(cited_fact(text, src, "high" if c.source_url else "medium"))
    return out


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    for f in run("Neon", "neon.tech"):
        print(f.confidence, "-", f.text, "-", f.source)
