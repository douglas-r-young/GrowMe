"""Pre-warm research fixtures for the hackathon demo.

Runs `growme.research.node.run` live for each demo combo and persists the
result via the existing `_write_fixture`. After running this once, the demo
can set USE_LIVE_RESEARCH=false and skip Apify entirely for known orgs.

Usage:
    USE_LIVE_RESEARCH=true python scripts/prewarm_fixtures.py
"""
from __future__ import annotations

import os
import sys
import time

from dotenv import load_dotenv

from growme.research.node import run as run_research
from growme.schemas import WizardInputs

# Each entry pre-warms one (alias, sorted-behavior-id-tuple) fixture.
# Add more demo orgs here. company_url is informational — research currently
# always runs against the hardcoded REAL_COMPANY in node.py and aliases after.
DEMO_COMBOS: list[dict] = [
    {
        "company_url": "neon.tech",
        "company_alias": "Photon DB",
        "audience_description": "12 mid-market AEs, 1-3 yrs tenure",
        "selected_behavior_ids": [
            "pic_pbo_quantify_pain",
            "pic_rc_capabilities_outcomes",
            "pic_diff_differentiate",
        ],
    },
]


def main() -> int:
    load_dotenv()
    os.environ["USE_LIVE_RESEARCH"] = "true"  # force live for the warm step

    for i, combo in enumerate(DEMO_COMBOS, 1):
        inputs = WizardInputs(**combo)
        print(f"\n[{i}/{len(DEMO_COMBOS)}] {inputs.company_alias} "
              f"behaviors={inputs.selected_behavior_ids}")
        t0 = time.time()
        try:
            ctx = run_research(inputs)
        except Exception as e:
            print(f"  FAILED: {e}")
            continue
        dt = time.time() - t0
        print(f"  OK in {dt:.1f}s — {len(ctx.sources_used)} sources, "
              f"{len(ctx.per_behavior)} behaviors")

    print("\nDone. Set USE_LIVE_RESEARCH=false to use the warmed fixtures.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
