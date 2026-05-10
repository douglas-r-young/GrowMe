"""Pedagogy compliance tests (per pedagogy v3 doc §10 anti-slop checklist).

Two layers:

1. **Fast unit checks** (run by default): validate the deterministic pieces —
   fixtures emit valid commitments, offline generators pass the new validators,
   schema validators fire on the right inputs, swap-test logic is sound.

2. **End-to-end pipeline check** (opt-in via `RUN_PEDAGOGY_E2E=1`): runs the full
   pipeline against the cached Photon DB research fixture in offline-research
   mode (LLM calls are LIVE; only Apify is skipped). Asserts the per-program
   checklist items hold. Slow + requires API keys.

Run the e2e suite manually:
    USE_LIVE_RESEARCH=false RUN_PEDAGOGY_E2E=1 uv run pytest tests/test_pedagogy_compliance.py::test_e2e -v
"""
from __future__ import annotations

import os
import re

import pytest
from pydantic import ValidationError

from growme.assessment.fixtures import (
    LEARNER_PROFILES,
    post_responses,
    pre_responses,
    profile_for,
)
from growme.assessment.generator import generate_program_assessment_offline
from growme.pedagogy.checklist import (
    count_specifics,
    has_banned_activity_phrase,
    has_implementation_intention,
    swap_test,
)
from growme.schemas import (
    AssessmentResponse,
    Nudge,
    SessionDeck,
    SessionPlan,
    AgendaBlock,
)


# ============================================================================
# 1. Fast unit checks (run by default)
# ============================================================================


@pytest.mark.parametrize("profile", LEARNER_PROFILES)
def test_fixture_learners_have_stage_and_strength(profile):
    assert profile.stage_of_change in ("skeptic", "beginner", "practitioner")
    assert 1 <= profile.commitment_strength <= 5
    assert profile.learner_id and profile.learner_name


def test_learner_profile_distribution_per_pedagogy_v3():
    """Expect a plausible cohort: 2 skeptics, 4 beginners, 2 practitioners."""
    counts = {"skeptic": 0, "beginner": 0, "practitioner": 0}
    for p in LEARNER_PROFILES:
        counts[p.stage_of_change] += 1
    assert counts["skeptic"] == 2
    assert counts["beginner"] == 4
    assert counts["practitioner"] == 2


def test_post_response_fixtures_emit_implementation_intentions():
    bids = ["b1", "b2", "b3"]
    posts = post_responses("uuid-x", bids)
    assert len(posts) == 8
    for r in posts:
        assert r.commitment is not None
        # commitment is now a structured Commitment; render it for the regex check.
        assert has_implementation_intention(r.commitment.render()), (
            f"learner {r.learner_id} commitment fails implementation-intention check: "
            f"{r.commitment.render()!r}"
        )
        assert r.commitment.trigger and r.commitment.action


def test_pre_response_fixtures_have_no_commitment():
    bids = ["b1", "b2", "b3"]
    pres = pre_responses("uuid-x", bids)
    for r in pres:
        assert r.commitment is None


def test_offline_assessment_generator_commitments_are_implementation_intentions():
    """Per pedagogy v3 doc §10: every commitment_option must use 'When X, I will Y'.
    The offline path is the deterministic baseline; if it fails the validator,
    the live path is unreliable too."""
    bids = ["pic_pbo_quantify_pain", "pic_rc_capabilities_outcomes", "pic_diff_differentiate"]
    a = generate_program_assessment_offline(bids)
    for opt in a.commitment_options:
        assert has_implementation_intention(opt), f"commitment fails check: {opt!r}"


def test_session_plan_validator_rejects_no_buffer():
    with pytest.raises(ValidationError, match="buffer"):
        SessionPlan(
            session_number=1,
            title="No buffer",
            behavior_id=None,
            learning_objective="x" * 30,
            agenda=[
                AgendaBlock(name="Open", duration_min=5, description="...", bucket="story"),
                AgendaBlock(name="Teach", duration_min=12, description="...", bucket="framework"),
                AgendaBlock(name="Discuss", duration_min=15, description="...", bucket="discussion"),
                AgendaBlock(name="Practice", duration_min=18, description="...", bucket="activity"),
                AgendaBlock(name="Close", duration_min=10, description="...", bucket="activity"),
            ],
        )


def test_session_plan_validator_rejects_oversized_framework_block():
    with pytest.raises(ValidationError, match="12 min cap"):
        SessionPlan(
            session_number=1,
            title="Long teach",
            behavior_id=None,
            learning_objective="x" * 30,
            agenda=[
                AgendaBlock(name="Long teach", duration_min=15, description="...", bucket="framework"),
                AgendaBlock(name="Practice", duration_min=20, description="...", bucket="activity"),
                AgendaBlock(name="Discuss", duration_min=10, description="...", bucket="discussion"),
                AgendaBlock(name="Close", duration_min=8, description="...", bucket="activity"),
                AgendaBlock(name="Buffer", duration_min=7, description="...", bucket="buffer"),
            ],
        )


def test_swap_test_marks_unanchored_text_as_slop():
    """Anti-slop swap test: content with no behavior token has no grip."""
    generic = (
        "This session covers important sales behaviors. Reps will learn key "
        "frameworks and apply them in practice scenarios."
    )
    assert swap_test(generic, "MEDDIC", "Challenger") is True  # generic = slop

    specific = (
        "Use the MEDDIC qualification framework to ask the EB the budget "
        "question on every first call."
    )
    assert swap_test(specific, "MEDDIC", "Challenger") is False  # specific = not slop


def test_count_specifics_dedupes_and_is_case_insensitive():
    found = count_specifics(
        "Photon DB scales horizontally. PHOTON DB also supports Snowflake and BigQuery.",
        ["Photon DB", "Snowflake", "BigQuery", "photon db"],
    )
    assert found == 3  # Photon DB (deduped) + Snowflake + BigQuery


def test_banned_activity_phrases_blocked():
    assert has_banned_activity_phrase("Discuss this in pairs.")
    assert has_banned_activity_phrase("Share your thoughts with the group.")
    assert not has_banned_activity_phrase(
        "Pick your top open opp. Write the budget question you'd ask the EB on Monday's call."
    )


def test_nudge_schema_has_phase_beta_fields():
    """Regression guard for the schema additions."""
    n = Nudge(
        learner_id="L1",
        session_number=1,
        week_offset=3,
        manager_facing=False,
        stage_target="skeptic",
        email_subject="Your X commitment",
        email_body_md="x" * 50,
        slack_text="x" * 25,
        proof_point_used={"text": "p", "source": "g2:u", "confidence": "high"},
    )
    assert n.week_offset == 3
    assert n.manager_facing is False
    assert n.stage_target == "skeptic"


def test_session_deck_carries_manager_briefing_field():
    """Regression guard for SessionDeck.manager_briefing_md."""
    d = SessionDeck(
        title="t",
        behavior_ids=["a", "b", "c"],
        slides=[],
        facilitator_guide_md="# guide",
        manager_briefing_md="# manager briefing",
        pre_qr_url="http://x?kind=pre",
        post_qr_url="http://x?kind=post",
    )
    assert d.manager_briefing_md == "# manager briefing"


# ============================================================================
# 2. End-to-end pipeline check (opt-in)
# ============================================================================


_E2E_REASON = (
    "Set RUN_PEDAGOGY_E2E=1 to run the live pipeline test. Requires API keys "
    "(Featherless + OpenAI) and uses the cached Photon DB research fixture."
)


@pytest.mark.skipif(not os.getenv("RUN_PEDAGOGY_E2E"), reason=_E2E_REASON)
def test_e2e_pipeline_against_photon_db_fixture():
    """Full pedagogy-compliance pass. Loads cached research, generates everything."""
    os.environ.setdefault("USE_LIVE_RESEARCH", "false")

    from growme.assessment.generator import generate_program_assessment
    from growme.decks.builder import build_deck
    from growme.decks.llm import gen_facilitator_guide, gen_manager_briefing, plan_deck
    from growme.design_doc.node import run as run_design_doc
    from growme.nudges.node import generate_for_post_responses
    from growme.research.node import run as run_research
    from growme.schemas import WizardInputs
    from growme.sessions.plan_node import run as run_plan

    inputs = WizardInputs(
        company_url="neon.tech",
        company_alias="Photon DB",
        audience_description=(
            "12 mid-market AEs, 1-3 yrs tenure. They run discovery calls but "
            "don't quantify pain in business-impact terms. The comp plan rewards "
            "velocity over qualification; reps know they should ask 'how do you "
            "measure that?' but default to capability pitch under quota pressure."
        ),
        selected_behavior_ids=[
            "pic_pbo_quantify_pain",
            "pic_rc_capabilities_outcomes",
            "pic_diff_differentiate",
        ],
    )

    enriched = run_research(inputs)
    design_doc = run_design_doc(enriched, inputs)
    plan = run_plan(design_doc.full_markdown, enriched, inputs)
    assessment = generate_program_assessment(enriched, inputs)
    deck_plan = plan_deck(plan, enriched)
    guide_md = gen_facilitator_guide(plan, enriched, deck_plan=deck_plan)
    manager_briefing_md = gen_manager_briefing(plan, enriched, deck_plan, design_doc.full_markdown)
    deck = build_deck(
        plan=plan, enriched=enriched, deck_plan=deck_plan,
        pre_qr_url="http://x?kind=pre", post_qr_url="http://x?kind=post",
        facilitator_guide_md=guide_md,
        manager_briefing_md=manager_briefing_md,
        company_alias=inputs.company_alias,
    )
    posts = post_responses("e2e-test-uuid", inputs.selected_behavior_ids)
    nudges = generate_for_post_responses(posts, enriched)

    # ----- Per-program anti-slop checklist (pedagogy v3 doc §10) -----

    # 1. Transfer plan exists
    assert "Transfer plan" in design_doc.full_markdown
    assert design_doc.transfer_plan_md.strip()

    # 2. Framework time ≤ 30%
    total = sum(b.duration_min for b in plan.agenda)
    fw = sum(b.duration_min for b in plan.agenda if b.bucket == "framework")
    assert fw / total <= 0.30, f"framework ratio {fw}/{total}"

    # 3. Buffer block exists with ≥ 5 min
    buffers = [b for b in plan.agenda if b.bucket == "buffer" and b.duration_min >= 5]
    assert buffers, "no buffer block ≥ 5 min"

    # 4. Commitment options use implementation-intention form
    for opt in assessment.commitment_options:
        assert has_implementation_intention(opt), f"non-II option: {opt!r}"

    # 5. Manager briefing present
    assert deck.manager_briefing_md and len(deck.manager_briefing_md) > 400

    # 6. Multi-week nudge schedule spans expected weeks
    learner_facing = [n for n in nudges if not n.manager_facing]
    manager_facing = [n for n in nudges if n.manager_facing]
    assert {n.week_offset for n in learner_facing} == {1, 3, 5, 7}, (
        f"got weeks {sorted({n.week_offset for n in learner_facing})}"
    )
    # 1 manager-facing nudge per learner with a commitment (8 of 8 in the fixture).
    assert len(manager_facing) == 8

    # 7. Stage-of-change diversity in nudge tones
    assert {n.stage_target for n in nudges} == {"skeptic", "beginner", "practitioner"}

    # 8. At least one slide per behavior references something from research
    for bc in enriched.per_behavior:
        bc_terms = (
            [bc.behavior_name]
            + [bc.framework_origin]
            + [f.text[:40] for f in bc.findings.examples[:3]]
            + [f.text[:40] for f in bc.findings.proof_points[:3]]
        )
        deck_text = " ".join(
            (s.title or "") + " " + str(s.blocks) + " " + (s.speaker_notes or "")
            for s in deck.slides
        )
        hits = sum(1 for t in bc_terms if t and t in deck_text)
        assert hits >= 1, f"behavior {bc.behavior_name!r}: no grounding in deck"

    # 9. Swap test: deck text references the company alias (anti-slop signal)
    deck_text = " ".join((s.title or "") + " " + str(s.blocks) for s in deck.slides)
    # Photon DB should appear at least once (cover, divider, or example).
    assert "Photon DB" in deck_text, "deck makes no reference to the company alias"
