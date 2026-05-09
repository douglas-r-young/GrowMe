"""Apify google-search-scraper wrapper. Returns trimmed results suitable for LLM context.

Public API matches the previous Tavily wrapper shape so callers don't change.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from apify_client import ApifyClient


@dataclass
class WebHit:
    url: str
    title: str
    content: str   # snippet, ~200-300 chars


def search(query: str, max_results: int = 5) -> list[WebHit]:
    client = ApifyClient(token=os.environ["APIFY_TOKEN"])
    run = client.actor("apify/google-search-scraper").call(
        run_input={
            "queries": query,
            "resultsPerPage": max_results,
            "maxPagesPerQuery": 1,
        },
    )
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    out: list[WebHit] = []
    for page in items:
        for r in (page.get("organicResults") or [])[:max_results]:
            out.append(WebHit(
                url=r.get("url", ""),
                title=r.get("title", ""),
                content=(r.get("description") or "")[:600],
            ))
            if len(out) >= max_results:
                break
        if len(out) >= max_results:
            break
    return out[:max_results]
