"""Generate multi-week nudges per post-assessment response.

V0 Phase β cadence (per pedagogy v3 doc §7 Transfer of Training):
- 4 learner-facing nudges per learner at week_offsets (1, 3, 5, 7), tone-shifted
  by the learner's stage_of_change (skeptic / beginner / practitioner).
- 1 manager-facing nudge per learner at week_offset=2 directing the manager
  to ask about the rep's commitment in their 1:1.
- 8 learners × 5 nudges = 40 total nudges per full simulation. Concurrency
  limited via the existing _PROVIDER_LIMITS semaphore (Featherless caps at 4).

The NUDGE_SYSTEM prompt comes from `growme.pedagogy` — pre-empts relapse,
references the commitment trigger and action verbatim, asks for evidence (not
feelings), closes with one beat the manager can ask in their 1:1.
"""
from __future__ import annotations

import random
from concurrent.futures import ThreadPoolExecutor

from pydantic import BaseModel, Field

from growme.assessment.fixtures import profile_for
from growme.llm_clients import complete_json
from growme.pedagogy import NUDGE_PRINCIPLES
from growme.schemas import (
    AssessmentResponse,
    BehaviorContext,
    CitedFact,
    Commitment,
    EnrichedContext,
    Nudge,
)


class _NudgePair(BaseModel):
    email_subject: str
    email_body_md: str = Field(min_length=40)
    slack_text: str = Field(min_length=20)


NUDGE_SYSTEM = f"""\
You write a post-training nudge for a sales rep OR for the rep's manager
(depending on the AUDIENCE field in the input).

Inputs in the user message:
  - AUDIENCE: "rep" or "manager"
  - COMMITMENT TRIGGER: the cue the rep's behavior fires on
  - COMMITMENT ACTION: the specific action the rep pledged
  - COMMITMENT (full): the rendered "When [trigger], I will [action]" form
  - PROOF POINT: a fact from the company's research the nudge can cite
  - WEEK: int (1, 3, 5, or 7) — which post-session week this nudge fires
  - STAGE: "skeptic" / "beginner" / "practitioner" — calibrate tone

Output strict JSON with:
  email_subject: short, second-person. For AUDIENCE=rep: "Your X commitment...".
    For AUDIENCE=manager: "1:1 prompt: ask [rep first name] about X".
  email_body_md: 60-100 words. For AUDIENCE=rep: reference the trigger AND
    the action separately ("When [trigger]... did you [action]?"); cite the
    proof point; close with one beat the manager can ask in their 1:1. For
    AUDIENCE=manager: write 2-3 specific questions the manager can ask in
    their 1:1 this week, grounded in the trigger + action.
  slack_text: 20-40 words. For AUDIENCE=rep: ask for evidence ("Did you [action]
    this week? Y/N"). For AUDIENCE=manager: a one-line nudge to surface the
    question in the upcoming 1:1.

{NUDGE_PRINCIPLES}
"""


def _pick_proof(per_behavior: list[BehaviorContext], rng: random.Random) -> CitedFact | None:
    pool = [pp for bc in per_behavior for pp in bc.findings.proof_points]
    if not pool:
        return None
    return rng.choice(pool)


def _make_nudge_text(
    *,
    audience: str,
    commitment: Commitment | None,
    proof_text: str,
    week: int,
    stage: str,
) -> _NudgePair:
    if commitment is None:
        trigger = "(no commitment recorded)"
        action = "(no action recorded)"
        rendered = "(no commitment recorded)"
    else:
        trigger = commitment.trigger
        action = commitment.action
        rendered = commitment.render()
    user = (
        f"AUDIENCE: {audience}\n"
        f"COMMITMENT TRIGGER: {trigger}\n"
        f"COMMITMENT ACTION: {action}\n"
        f"COMMITMENT (full): {rendered}\n"
        f"PROOF POINT: {proof_text}\n"
        f"WEEK: {week}\n"
        f"STAGE: {stage}\n"
    )
    return complete_json(role="nudges", system=NUDGE_SYSTEM, user=user, schema=_NudgePair)


def _build_one_nudge(
    *,
    response: AssessmentResponse,
    enriched: EnrichedContext,
    week_offset: int,
    manager_facing: bool,
    rng: random.Random,
) -> Nudge:
    profile = profile_for(response.learner_id)
    proof = _pick_proof(enriched.per_behavior, rng)
    proof_text = proof.text if proof else "Use a recent customer outcome to anchor your message."
    pair = _make_nudge_text(
        audience="manager" if manager_facing else "rep",
        commitment=response.commitment,
        proof_text=proof_text,
        week=week_offset,
        stage=profile.stage_of_change,
    )
    return Nudge(
        learner_id=response.learner_id,
        session_number=1,
        week_offset=week_offset,
        manager_facing=manager_facing,
        stage_target=profile.stage_of_change,
        email_subject=pair.email_subject,
        email_body_md=pair.email_body_md,
        slack_text=pair.slack_text,
        proof_point_used=proof or CitedFact(
            text=proof_text, source="inference:nudges", confidence="low",
        ),
    )


# Manager-facing nudge fires once per learner, at week 2 (between week-1 and
# week-3 learner nudges) so the manager hears about it BEFORE the dip starts.
_MANAGER_NUDGE_WEEK = 2


def generate_for_post_responses(
    post_responses: list[AssessmentResponse],
    enriched: EnrichedContext,
    week_offsets: tuple[int, ...] = (1, 3, 5, 7),
    *,
    seed: int = 17,
) -> list[Nudge]:
    """Generate multi-week + manager-facing nudges. Returns a flat list[Nudge].

    For each post response with a recorded commitment:
      - One nudge per week_offset (default: 1, 3, 5, 7).
      - One manager-facing nudge at week _MANAGER_NUDGE_WEEK (default: 2).

    Calls run in parallel via ThreadPoolExecutor; the existing _PROVIDER_LIMITS
    semaphore in llm_clients gates concurrency by provider.
    """
    rng = random.Random(seed)
    eligible = [r for r in post_responses if r.kind == "post" and r.commitment]
    if not eligible:
        return []

    # Pre-compute work tickets so the rng is consumed deterministically (parallel
    # threads each pick their proof point independently from a shared rng wrapped
    # in a lock; we proxy that via per-ticket Random instances seeded from the
    # parent rng to keep proof selection stable across runs).
    tickets: list[tuple[AssessmentResponse, int, bool, random.Random]] = []
    for r in eligible:
        for w in week_offsets:
            tickets.append((r, w, False, random.Random(rng.random())))
        tickets.append((r, _MANAGER_NUDGE_WEEK, True, random.Random(rng.random())))

    nudges: list[Nudge] = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = [
            ex.submit(
                _build_one_nudge,
                response=r,
                enriched=enriched,
                week_offset=w,
                manager_facing=mf,
                rng=ticket_rng,
            )
            for (r, w, mf, ticket_rng) in tickets
        ]
        for fut in futures:
            try:
                nudges.append(fut.result())
            except Exception as e:  # one bad nudge shouldn't kill the cohort
                print(f"[nudges] generation failed for one nudge: {e}")

    # Sort: by learner, then learner-facing first by week, then manager-facing.
    nudges.sort(
        key=lambda n: (n.learner_id, 1 if n.manager_facing else 0, n.week_offset),
    )
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
    print(f"Generated {len(nudges)} nudges.\n")
    for n in nudges[:6]:
        tag = "MGR" if n.manager_facing else "REP"
        print(f"[{tag} · w{n.week_offset} · {n.stage_target}] {n.learner_id}: {n.email_subject}")
        print(f"  slack: {n.slack_text}\n")
