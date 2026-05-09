"""Live smoke test for Apify integrations. Hits neon.tech and pipeline.

Usage: python scripts/smoke_apify.py
"""
from dotenv import load_dotenv

load_dotenv()

from growme.research.apify_clients import run_website_crawler  # noqa: E402

print("--- website crawler on https://neon.tech ---")
items = run_website_crawler(["https://neon.tech"], max_pages=2)
print(f"got {len(items)} pages")
if items:
    sample = items[0]
    print(f"first url: {sample.get('url')}")
    print(f"first text len: {len(sample.get('text') or sample.get('markdown') or '')}")
