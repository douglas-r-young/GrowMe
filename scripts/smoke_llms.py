"""Run a single completion against each provider to verify keys + connectivity.

Usage: python scripts/smoke_llms.py
"""
from dotenv import load_dotenv

load_dotenv()

from growme.llm_clients import complete  # noqa: E402

PROMPT = "Say the single word OK."

for role in ["research_extract", "design_doc", "session_plan"]:
    print(f"\n--- {role} ---")
    out = complete(role, system="You are a terse assistant.", user=PROMPT, max_tokens=10)
    print(out.strip())
