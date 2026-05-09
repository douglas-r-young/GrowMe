"""Apify google-search-scraper wrapper. Returns trimmed results suitable for LLM context.

Public API matches the previous Tavily wrapper shape so callers don't change.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from apify_client import ApifyClient

from growme.research.apify_throttle import apify_slot

_ACTOR_MEMORY_MB = 1024


@dataclass
class WebHit:
    url: str
    title: str
    content: str   # snippet, ~200-300 chars


def search(query: str, max_results: int = 5) -> list[WebHit]:
    return search_many([query], max_results=max_results).get(query, [])


def search_many(queries: list[str], max_results: int = 5) -> dict[str, list[WebHit]]:
    """Run google-search-scraper once with N queries; return {query: [WebHit]}.

    The Actor accepts queries newline-separated and tags each output page with
    `searchQuery.term` so we can group results back per input query. This
    collapses N cold-starts into 1 — the dominant cost in Phase B.
    """
    if not queries:
        return {}
    client = ApifyClient(token=os.environ["APIFY_TOKEN"])
    queries_input = "\n".join(queries)
    with apify_slot(_ACTOR_MEMORY_MB):
        run = client.actor("apify/google-search-scraper").call(
            run_input={
                "queries": queries_input,
                "resultsPerPage": max_results,
                "maxPagesPerQuery": 1,
            },
            memory_mbytes=_ACTOR_MEMORY_MB,
        )
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    grouped: dict[str, list[WebHit]] = {q: [] for q in queries}
    for page in items:
        term = (page.get("searchQuery") or {}).get("term", "")
        bucket = grouped.get(term)
        if bucket is None:
            # Actor's term may differ slightly from input (whitespace/casing).
            # Fall back to nearest exact match by substring.
            match = next((q for q in queries if q.strip() == term.strip()), None)
            bucket = grouped.setdefault(match, []) if match else None
        if bucket is None:
            continue
        for r in (page.get("organicResults") or [])[:max_results]:
            if len(bucket) >= max_results:
                break
            bucket.append(WebHit(
                url=r.get("url", ""),
                title=r.get("title", ""),
                content=(r.get("description") or "")[:600],
            ))
    return grouped
