"""Generate a DesignDoc from EnrichedContext + WizardInputs.

V0 ships ONE 60-minute integration session. The DesignDoc schema collapsed on
2026-05-09 to match (single `integration_learning_objective`, mandatory
`transfer_plan_md`). See schemas.py:DesignDoc for the rationale.
"""
from __future__ import annotations

import logging

from growme.design_doc.prompts import DESIGN_DOC_SYSTEM, build_user_prompt
from growme.llm_clients import complete_json
from growme.pedagogy.checklist import count_specifics
from growme.schemas import DesignDoc, EnrichedContext, WizardInputs

_log = logging.getLogger(__name__)


def run(enriched: EnrichedContext, inputs: WizardInputs) -> DesignDoc:
    enriched_json = enriched.model_dump_json()
    user = build_user_prompt(
        enriched_json=enriched_json,
        audience=inputs.audience_description,
        duration_min=inputs.session_duration_min,
    )
    doc = complete_json(
        role="design_doc",
        system=DESIGN_DOC_SYSTEM,
        user=user,
        schema=DesignDoc,
        max_tokens=3000,
    )
    # Post-hoc anti-slop check that needs the enriched context to evaluate.
    # Pydantic context-aware validators don't run inside complete_json's retry
    # loop (the loop calls model_validate_json without context), so we run this
    # ourselves and warn rather than fail — the retry pressure already pushed
    # the model toward compliance via the prompt.
    specifics = (
        list(enriched.base.vertical_vocab)
        + [c.text for c in enriched.base.named_competitors]
        + [c.text for c in enriched.base.customer_voice]
    )
    n_specifics = count_specifics(doc.full_markdown, specifics)
    if n_specifics < 3:
        _log.warning(
            "design_doc.full_markdown references only %d/%d possible research specifics; "
            "anti-slop target is ≥3. Doc will ship but consider regenerating.",
            n_specifics, len(specifics),
        )
    return doc


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    from growme.research.node import run as run_research
    inputs = WizardInputs(
        company_url="neon.tech",
        company_alias="Photon DB",
        audience_description="12 mid-market AEs, 1-3 yrs tenure",
        selected_behavior_ids=[
            "pic_pbo_quantify_pain",
            "pic_rc_capabilities_outcomes",
            "pic_diff_differentiate",
        ],
    )
    enriched = run_research(inputs)
    doc = run(enriched, inputs)
    print(doc.full_markdown)
