"""Thin wrappers over Apify Actors used in research."""
from __future__ import annotations

import os
from typing import Any

from apify_client import ApifyClient

from growme.research.apify_throttle import apify_slot

# Playwright-based crawler needs Chromium headroom; 1024 MB OOM-kills it.
_CRAWLER_MEMORY_MB = 4096
_G2_MEMORY_MB = 1024


def _client() -> ApifyClient:
    return ApifyClient(token=os.environ["APIFY_TOKEN"])


def run_website_crawler(start_urls: list[str], max_pages: int = 5) -> list[dict[str, Any]]:
    """Apify website-content-crawler. Returns list of {url, text, ...} items."""
    actor = _client().actor("apify/website-content-crawler")
    with apify_slot(_CRAWLER_MEMORY_MB):
        run = actor.call(
            run_input={
                "startUrls": [{"url": u} for u in start_urls],
                "maxCrawlPages": max_pages,
                "saveMarkdown": True,
            },
            memory_mbytes=_CRAWLER_MEMORY_MB,
        )
    items = list(_client().dataset(run["defaultDatasetId"]).iterate_items())
    return items


def run_g2_scraper(product_url: str, max_reviews: int = 25) -> list[dict[str, Any]]:
    """Apify G2 scraper. Returns list of review items.

    Uses omkar-cloud/g2-product-scraper.
    """
    actor = _client().actor("omkar-cloud/g2-product-scraper")
    with apify_slot(_G2_MEMORY_MB):
        run = actor.call(
            run_input={
                "product_urls": [product_url],
                "max_reviews": max_reviews,
            },
            memory_mbytes=_G2_MEMORY_MB,
        )
    items = list(_client().dataset(run["defaultDatasetId"]).iterate_items())
    return items
