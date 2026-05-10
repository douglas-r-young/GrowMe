# src/growme/research/phase_a/orchestrator.py
"""Run all 4 Phase A branches in parallel and assemble BaseCompanyResearch."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from growme.research.phase_a import (
    company_snapshot,
    customer_voice,
    named_competitors,
    vertical_vocab,
)
from growme.schemas import BaseCompanyResearch


def run(company_url: str, company_alias: str, g2_product_url: str | None = None) -> BaseCompanyResearch:
    """Parallel execution of all 4 Phase A branches.

    g2_product_url may be None; if so, customer_voice is skipped (left empty).
    """
    tasks = {
        "snapshot": (company_snapshot.run, (company_url,)),
        "vocab":    (vertical_vocab.run, (company_url,)),
        "competitors": (named_competitors.run, (company_alias, company_url)),
    }
    if g2_product_url:
        tasks["voice"] = (customer_voice.run, (g2_product_url,))

    results: dict[str, object] = {}
    with ThreadPoolExecutor(max_workers=len(tasks)) as ex:
        future_to_key = {ex.submit(fn, *args): key for key, (fn, args) in tasks.items()}
        for fut in as_completed(future_to_key):
            key = future_to_key[fut]
            try:
                results[key] = fut.result()
            except Exception as e:
                print(f"[phase_a] {key} failed: {e}")
                results[key] = None

    return BaseCompanyResearch(
        company_snapshot=results.get("snapshot") or "",
        customer_voice=results.get("voice") or [],
        vertical_vocab=results.get("vocab") or [],
        named_competitors=results.get("competitors") or [],
    )


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    base = run(
        company_url="neon.tech",
        company_alias="Neon",
        g2_product_url="https://www.g2.com/products/neon/reviews",
    )
    print(base.model_dump_json(indent=2)[:2000])
