"""Generate a DesignDoc from EnrichedContext + WizardInputs."""
from __future__ import annotations

from growme.design_doc.prompts import DESIGN_DOC_SYSTEM, build_user_prompt
from growme.llm_clients import complete_json
from growme.schemas import DesignDoc, EnrichedContext, WizardInputs


def run(enriched: EnrichedContext, inputs: WizardInputs) -> DesignDoc:
    enriched_json = enriched.model_dump_json()
    # The design doc is generated against the *intended* 4-session curriculum
    # even when V0 collapses delivery to 1 session (program_length_sessions=1).
    user = build_user_prompt(
        enriched_json=enriched_json,
        audience=inputs.audience_description,
        sessions=4,
        duration_min=inputs.session_duration_min,
    )
    doc = complete_json(
        role="design_doc",
        system=DESIGN_DOC_SYSTEM,
        user=user,
        schema=DesignDoc,
        max_tokens=3000,
    )
    if len(doc.behavior_objectives) != 3 or len(doc.learning_objectives) != 4:
        raise ValueError(
            f"Design doc has wrong section lengths: "
            f"behaviors={len(doc.behavior_objectives)} (need 3), "
            f"learning={len(doc.learning_objectives)} (need 4)"
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
