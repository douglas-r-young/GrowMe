"""Generate one nudge per post-assessment response. Returns list[Nudge]."""
from __future__ import annotations

import random

from pydantic import BaseModel, Field

from growme.llm_clients import complete_json
from growme.schemas import (
    AssessmentResponse,
    BehaviorContext,
    CitedFact,
    EnrichedContext,
    Nudge,
)


class _NudgePair(BaseModel):
    email_subject: str
    email_body_md: str = Field(min_length=40)
    slack_text: str = Field(min_length=20)


NUDGE_SYSTEM = """\
You write a one-week post-training nudge for a sales rep.
Inputs: their COMMITMENT (a single concrete action they pledged), and a relevant
PROOF POINT (a fact about the company's product they should know).

Output strict JSON with:
  email_subject: short, second-person ("Your X commitment...")
  email_body_md: 60-100 words, encouraging, concrete; cite the proof point naturally
  slack_text: 20-40 words, casual, prompt them to reply yes/no on whether they did the action
"""


def _pick_proof(per_behavior: list[BehaviorContext]) -> CitedFact | None:
    pool = [pp for bc in per_behavior for pp in bc.findings.proof_points]
    if not pool:
        return None
    return random.choice(pool)


def _make_nudge_text(commitment: str, proof_text: str) -> _NudgePair:
    user = f"COMMITMENT: {commitment}\n\nPROOF POINT: {proof_text}\n"
    return complete_json(role="nudges", system=NUDGE_SYSTEM, user=user, schema=_NudgePair)


def generate_for_post_responses(
    post_responses: list[AssessmentResponse],
    enriched: EnrichedContext,
) -> list[Nudge]:
    nudges: list[Nudge] = []
    for r in post_responses:
        if r.kind != "post" or not r.commitment:
            continue
        proof = _pick_proof(enriched.per_behavior)
        proof_text = proof.text if proof else "Use a recent customer outcome to anchor your message."
        pair = _make_nudge_text(r.commitment, proof_text)
        nudges.append(Nudge(
            learner_id=r.learner_id,
            session_number=1,
            email_subject=pair.email_subject,
            email_body_md=pair.email_body_md,
            slack_text=pair.slack_text,
            proof_point_used=proof or CitedFact(
                text=proof_text, source="inference:nudges", confidence="low",
            ),
        ))
    return nudges


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    from growme.assessment.fixtures import post_responses
    from growme.research.node import run as run_research
    from growme.schemas import WizardInputs
    inputs = WizardInputs(
        company_url="neon.tech", company_alias="Photon DB",
        audience_description="12 mid-market AEs",
        selected_behavior_ids=[
            "pic_pbo_quantify_pain",
            "pic_rc_capabilities_outcomes",
            "pic_diff_differentiate",
        ],
    )
    ec = run_research(inputs)
    posts = post_responses("smoke", inputs.selected_behavior_ids)
    nudges = generate_for_post_responses(posts, ec)
    for n in nudges:
        print(f"\n[{n.learner_id}] {n.email_subject}")
        print(n.slack_text)
