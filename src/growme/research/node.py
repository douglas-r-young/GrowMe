"""Top-level research node. Runs Phase A + Phase B in parallel and aliases output.

Usage from LangGraph:
    state["enriched_context"] = run(state["wizard_inputs"])
"""
from __future__ import annotations

import datetime
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from growme.research.aliasing import alias_obj
from growme.research.phase_a.orchestrator import run as run_phase_a
from growme.research.phase_b.behavior_research import run as run_phase_b
from growme.schemas import EnrichedContext, WizardInputs

REAL_COMPANY = "Neon"
REAL_URL = "neon.tech"
G2_URL = "https://www.g2.com/products/neon/reviews"

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def run(inputs: WizardInputs) -> EnrichedContext:
    """Run live or load from fixture cache based on USE_LIVE_RESEARCH."""
    use_live = os.environ.get("USE_LIVE_RESEARCH", "true").lower() == "true"
    if not use_live:
        cached = _try_load_fixture(inputs)
        if cached is not None:
            return cached

    base_future_args = (REAL_URL, REAL_COMPANY, G2_URL)
    behavior_args = inputs.selected_behavior_ids

    with ThreadPoolExecutor(max_workers=4) as ex:
        base_future = ex.submit(run_phase_a, *base_future_args)
        beh_futures = {ex.submit(run_phase_b, bid, REAL_COMPANY): bid for bid in behavior_args}

        base = base_future.result()
        per_behavior_by_id: dict[str, object] = {}
        for fut in as_completed(beh_futures):
            bid = beh_futures[fut]
            per_behavior_by_id[bid] = fut.result()

    # Preserve user-selected order
    per_behavior = [per_behavior_by_id[bid] for bid in behavior_args]

    sources: list[str] = []
    for cf in base.customer_voice + base.named_competitors:
        sources.append(cf.source)
    for bc in per_behavior:
        for bucket in (bc.findings.examples, bc.findings.baselines,
                       bc.findings.objections, bc.findings.proof_points):
            for cf in bucket:
                sources.append(cf.source)

    enriched = EnrichedContext(
        base=base,
        per_behavior=per_behavior,
        sources_used=sorted(set(sources)),
        research_timestamp=datetime.datetime.utcnow().isoformat() + "Z",
    )

    # Alias the whole tree (Neon → Photon DB / neon.tech → photondb.io)
    aliased_dict = alias_obj(
        enriched.model_dump(),
        REAL_COMPANY, inputs.company_alias,
        REAL_URL, _alias_url(inputs.company_alias),
    )
    aliased = EnrichedContext.model_validate(aliased_dict)

    _write_fixture(inputs, aliased)
    return aliased


def _alias_url(alias: str) -> str:
    """Cheap alias-URL guess: lowercase + '.io'. Override per project if needed."""
    return alias.lower().replace(" ", "") + ".io"


def _fixture_path(inputs: WizardInputs) -> Path:
    key = "_".join(sorted(inputs.selected_behavior_ids))
    return FIXTURES_DIR / f"{inputs.company_alias.lower().replace(' ', '_')}__{key}.json"


def _try_load_fixture(inputs: WizardInputs) -> EnrichedContext | None:
    p = _fixture_path(inputs)
    if not p.exists():
        return None
    return EnrichedContext.model_validate_json(p.read_text())


def _write_fixture(inputs: WizardInputs, ctx: EnrichedContext) -> None:
    FIXTURES_DIR.mkdir(exist_ok=True)
    p = _fixture_path(inputs)
    p.write_text(ctx.model_dump_json(indent=2))


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    inp = WizardInputs(
        company_url="neon.tech",
        company_alias="Photon DB",
        audience_description="12 mid-market AEs",
        selected_behavior_ids=[
            "pic_pbo_quantify_pain",
            "pic_rc_capabilities_outcomes",
            "pic_diff_differentiate",
        ],
    )
    out = run(inp)
    print(out.model_dump_json(indent=2)[:3000])
    print(f"\n--- {len(out.sources_used)} unique sources ---")
