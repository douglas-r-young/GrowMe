"""Factory + helpers for CitedFact provenance."""
from __future__ import annotations

from typing import Literal

from growme.schemas import CitedFact


def cited_fact(text: str, source: str, confidence: Literal["high", "medium", "low"] | None = None) -> CitedFact:
    """Default confidence is 'high' if source has a URL; 'medium' otherwise."""
    if confidence is None:
        confidence = "high" if any(p in source for p in (":http", ".com", ".io", ".net")) else "medium"
    return CitedFact(text=text, source=source, confidence=confidence)


def source_g2(url: str) -> str:
    return f"g2:{url}"


def source_web(url: str) -> str:
    return f"web:{url}"


def source_wizard(field: str) -> str:
    return f"wizard:{field}"


def source_apify_crawl(url: str) -> str:
    return f"apify_crawl:{url}"


def source_inference(model_role: str) -> str:
    return f"inference:{model_role}"
