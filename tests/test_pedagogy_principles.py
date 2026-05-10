"""Pedagogy package smoke + integration tests.

Asserts:
1. Every bundle constant is non-empty and bounded so we don't blow the system
   prompt budget.
2. Every generation system prompt carries a sentinel string from its bundle —
   confirms the bundle was actually concatenated (not lost in a refactor).
3. Anti-slop helper functions behave correctly on canonical inputs.
"""
from __future__ import annotations

import pytest

from growme.pedagogy import (
    ANTI_SLOP_TAIL,
    ASSESSMENT_PRINCIPLES,
    BEHAVIOR_ALTITUDE_PRINCIPLES,
    DECK_PEDAGOGY_NON_NEGOTIABLES,
    DESIGN_DOC_PRINCIPLES,
    GUIDE_FACILITATION_PRINCIPLES,
    HUMAN_HANDOFF_PRINCIPLES,
    IMPLEMENTATION_INTENTION_RULES,
    MANAGER_BRIEFING_PRINCIPLES,
    NUDGE_PRINCIPLES,
    PACING_PRINCIPLES,
    SESSION_PLAN_PRINCIPLES,
    STAGE_OF_CHANGE_PRINCIPLES,
    TRANSFER_PRINCIPLES,
)
from growme.pedagogy.checklist import (
    PER_PROGRAM_CHECKS,
    PER_SESSION_CHECKS,
    count_specifics,
    has_banned_activity_phrase,
    has_implementation_intention,
    swap_test,
)


# ============================================================================
# 1. Bundle size + content
# ============================================================================


_BUNDLES = {
    "ANTI_SLOP_TAIL": ANTI_SLOP_TAIL,
    "BEHAVIOR_ALTITUDE_PRINCIPLES": BEHAVIOR_ALTITUDE_PRINCIPLES,
    "IMPLEMENTATION_INTENTION_RULES": IMPLEMENTATION_INTENTION_RULES,
    "STAGE_OF_CHANGE_PRINCIPLES": STAGE_OF_CHANGE_PRINCIPLES,
    "TRANSFER_PRINCIPLES": TRANSFER_PRINCIPLES,
    "PACING_PRINCIPLES": PACING_PRINCIPLES,
    "HUMAN_HANDOFF_PRINCIPLES": HUMAN_HANDOFF_PRINCIPLES,
    "DESIGN_DOC_PRINCIPLES": DESIGN_DOC_PRINCIPLES,
    "SESSION_PLAN_PRINCIPLES": SESSION_PLAN_PRINCIPLES,
    "DECK_PEDAGOGY_NON_NEGOTIABLES": DECK_PEDAGOGY_NON_NEGOTIABLES,
    "GUIDE_FACILITATION_PRINCIPLES": GUIDE_FACILITATION_PRINCIPLES,
    "ASSESSMENT_PRINCIPLES": ASSESSMENT_PRINCIPLES,
    "NUDGE_PRINCIPLES": NUDGE_PRINCIPLES,
    "MANAGER_BRIEFING_PRINCIPLES": MANAGER_BRIEFING_PRINCIPLES,
}


@pytest.mark.parametrize("name,bundle", list(_BUNDLES.items()))
def test_bundle_non_empty_and_bounded(name: str, bundle: str):
    assert isinstance(bundle, str), f"{name} must be a str"
    assert len(bundle) > 200, f"{name} suspiciously short ({len(bundle)} chars)"
    # Role bundles compose 3-4 shared bundles plus role-specific text — they can
    # legitimately reach ~5000 chars. Cap at 6000 to catch runaway concatenation.
    assert len(bundle) < 6000, f"{name} too large ({len(bundle)} chars)"


# ============================================================================
# 2. Sentinels in each generation system prompt
# ============================================================================


def test_design_doc_system_carries_principles():
    from growme.design_doc.prompts import DESIGN_DOC_SYSTEM
    for sentinel in ("Transfer plan", "altitude", "next Tuesday"):
        assert sentinel in DESIGN_DOC_SYSTEM, f"DESIGN_DOC_SYSTEM missing: {sentinel!r}"


def test_session_plan_system_carries_principles():
    from growme.sessions.plan_node import SESSION_PLAN_SYSTEM
    for sentinel in ("Two-thirds", "Block floors", "Buffer + breathing room"):
        assert sentinel in SESSION_PLAN_SYSTEM, f"SESSION_PLAN_SYSTEM missing: {sentinel!r}"


def test_planner_system_carries_pedagogy_non_negotiables():
    from growme.decks.llm import PLANNER_SYSTEM
    for sentinel in (
        "Story stems",
        "Calibration question",
        "Anti-pattern",
        "fictional company",
        "swap test",
    ):
        assert sentinel in PLANNER_SYSTEM, f"PLANNER_SYSTEM missing: {sentinel!r}"


def test_guide_system_carries_facilitation_principles():
    from growme.decks.llm import GUIDE_SYSTEM
    for sentinel in ("Wait time", "Story slot scripts", "Buffer is on schedule"):
        assert sentinel in GUIDE_SYSTEM, f"GUIDE_SYSTEM missing: {sentinel!r}"


def test_assessment_system_carries_principles():
    from growme.assessment.generator import ASSESSMENT_SYSTEM
    for sentinel in ("Behavior, not confidence", "When [specific trigger]"):
        assert sentinel in ASSESSMENT_SYSTEM, f"ASSESSMENT_SYSTEM missing: {sentinel!r}"


def test_nudge_system_carries_principles():
    from growme.nudges.node import NUDGE_SYSTEM
    for sentinel in ("relapse", "Stage-aware", "manager can ask"):
        assert sentinel in NUDGE_SYSTEM, f"NUDGE_SYSTEM missing: {sentinel!r}"


def test_synth_system_flags_resistance_patterns():
    from growme.research.phase_b.behavior_research import SYNTH_SYSTEM
    for sentinel in ("skill gap", "incentive mismatch", "fear"):
        assert sentinel in SYNTH_SYSTEM, f"SYNTH_SYSTEM missing: {sentinel!r}"


# ============================================================================
# 3. Helper functions
# ============================================================================


@pytest.mark.parametrize("text", [
    "When pipeline review starts, I will state the EB name",
    "When I open Salesforce, I'll fill in the EB field",
    "When my Tuesday demo ends, I will note 3 budget questions in the deal record",
    # Habit-stack cues — pedagogy/principles.py explicitly endorses these
    "Before Tuesday's pipeline review, I will pre-write the EB name for each open opp",
    "After my next discovery call ends, I will log 2 proof points against the top competitor",
    "If a prospect names a competitor on a call, I will state our differentiator before they finish framing",
    "Once the demo wraps, I'll send the proof-point follow-up within the hour",
])
def test_implementation_intention_accepts_well_formed(text: str):
    assert has_implementation_intention(text), f"should accept: {text!r}"


@pytest.mark.parametrize("text", [
    "I commit to using MEDDIC",
    "When I have time, I will work on this",
    "Whenever I remember, I will quantify pain",
    "During the week, I will ask the budget question",
    "After a while, I will get to it",
    "Before too long, I will start practicing",
    "",
    "Just qualify better",
])
def test_implementation_intention_rejects_malformed(text: str):
    assert not has_implementation_intention(text), f"should reject: {text!r}"


def test_count_specifics_case_insensitive_and_dedupes():
    text = "We use Photon DB and Snowflake — Photon DB is fast"
    found = count_specifics(text, ["Photon DB", "Snowflake", "BigQuery", "photon db"])
    # "Photon DB" and "photon db" are dedupe-equal; should count Photon DB + Snowflake = 2
    assert found == 2


def test_swap_test_signals_slop():
    # Content with no behavior token has no grip → IS slop.
    assert swap_test("This is generic training content", "MEDDIC", "Challenger") is True
    # Content that uses the token has grip → NOT slop.
    assert swap_test("MEDDIC qualification on every call", "MEDDIC", "Challenger") is False


def test_has_banned_activity_phrase():
    assert has_banned_activity_phrase("Discuss this in pairs") is True
    assert has_banned_activity_phrase("Share your thoughts") is True
    assert has_banned_activity_phrase("Pair up and write the EB question for your top 3 deals") is False


def test_checklists_loaded():
    assert len(PER_SESSION_CHECKS) >= 10
    assert len(PER_PROGRAM_CHECKS) >= 9
    # Every check has a non-empty id + description + valid severity
    for c in PER_SESSION_CHECKS + PER_PROGRAM_CHECKS:
        assert c.check_id and c.description
        assert c.severity in ("minor", "major")


# ============================================================================
# 4. DesignDoc schema collapsed to 1-session
# ============================================================================


def test_design_doc_no_longer_has_learning_objectives_field():
    """Regression guard. The 4-session structure was dropped on 2026-05-09."""
    from growme.schemas import DesignDoc
    fields = DesignDoc.model_fields
    assert "learning_objectives" not in fields, (
        "Schema should no longer carry the 4-session learning_objectives list"
    )
    assert "integration_learning_objective" in fields
    assert "transfer_plan_md" in fields


def test_design_doc_rejects_missing_transfer_plan_heading():
    from pydantic import ValidationError
    from growme.schemas import DesignDoc
    with pytest.raises(ValidationError, match="Transfer plan"):
        DesignDoc(
            audience_section_md="x" * 100,
            behavior_objectives=["a", "b", "c"],
            integration_learning_objective="After this 60-min session reps will integrate three behaviors.",
            transfer_plan_md="x" * 100,
            full_markdown="# Audience\n\nNo transfer plan here at all.",
        )


def test_design_doc_accepts_transfer_plan_heading():
    from growme.schemas import DesignDoc
    d = DesignDoc(
        audience_section_md="x" * 100,
        behavior_objectives=["a", "b", "c"],
        integration_learning_objective="After this 60-min session reps will integrate three behaviors and ground them in customer outcomes.",
        transfer_plan_md=(
            "The transfer plan body covers triggers, cadence over 6-8 weeks weighted "
            "toward weeks 2-6, manager 1:1 role, failure modes for this audience, and "
            "what evidence proves behavior changed."
        ),
        full_markdown="# Audience\n\n## Transfer plan\n\nWeeks 2-6 nudges...",
    )
    assert d.behavior_objectives == ["a", "b", "c"]
