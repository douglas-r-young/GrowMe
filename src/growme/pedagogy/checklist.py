"""Anti-slop checklist as structured Python data + helper functions.

Source: `full_context.md` §10 (anti-slop checklist). The structured data is what
the LLM auditor in `auditor.py` (Phase γ) iterates over. The helper functions
power deterministic Pydantic validators and the test_pedagogy_compliance suite.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CheckItem:
    """One item from the per-session or per-program anti-slop checklist."""
    check_id: str
    description: str
    severity: str  # "minor" | "major"


PER_SESSION_CHECKS: list[CheckItem] = [
    CheckItem(
        "real_situation",
        "Names a real situation. Not 'feedback is important' but a specific scenario the audience faces.",
        "major",
    ),
    CheckItem(
        "anchored_in_context",
        "Anchored to user context. References at least 3 specifics from the user's research (real customer phrases, vocab terms, competitors, named products).",
        "major",
    ),
    CheckItem(
        "sme_story_stem",
        "Has SME story slot with tight stem. 60-90 seconds answerable, with tension, ≥3 minutes total airtime, marked [SME story slot].",
        "major",
    ),
    CheckItem(
        "live_practice_artifact",
        "Has live practice that produces an artifact. Real draft, commitment, or calendar block — not 'discuss this'.",
        "major",
    ),
    CheckItem(
        "structured_discussion_time",
        "Has structured discussion with adequate time. ≥6 min pair, ≥10 min small group.",
        "minor",
    ),
    CheckItem(
        "implementation_intention",
        "Commitment uses implementation-intention structure. 'When X, I will Y' with concrete trigger and action.",
        "major",
    ),
    CheckItem(
        "framework_time_cap",
        "Framework time ≤30%. No single block exceeds 12 minutes uninterrupted.",
        "major",
    ),
    CheckItem(
        "two_thirds_fill",
        "Two-thirds time fill. Doesn't pack 95% of available time. Buffer block is labeled and ≥5 min.",
        "minor",
    ),
    CheckItem(
        "silent_reflection",
        "Includes silent reflection. ≥30 seconds, intentional and labeled.",
        "minor",
    ),
    CheckItem(
        "no_fictional_companies",
        "No fictional company case studies. SME stories or [Real customer name — facilitator inserts] only.",
        "major",
    ),
    CheckItem(
        "human_handoff_marked",
        "Human-handoff slots marked clearly. Program owner knows what to source ([SME story slot], [Program owner customizes], etc.).",
        "major",
    ),
]


PER_PROGRAM_CHECKS: list[CheckItem] = [
    CheckItem(
        "behavior_altitude",
        "Behavior is at the right altitude. Specific, observable, executable next Tuesday.",
        "major",
    ),
    CheckItem(
        "resistance_pattern_named",
        "Resistance pattern is named. Skill, habit, incentive, fear, or environment — at least one identified.",
        "major",
    ),
    CheckItem(
        "mager_pipe_diagnostic",
        "Mager/Pipe diagnostic passed. If they could do it under threat, training is wrong intervention; flag this.",
        "major",
    ),
    CheckItem(
        "stage_diversity",
        "Stages-of-change diversity addressed. Content works for skeptics, not just for the prepared.",
        "minor",
    ),
    CheckItem(
        "transfer_plan_section",
        "Transfer plan section exists. Behavior, trigger, cadence, manager role, failure modes, evidence.",
        "major",
    ),
    CheckItem(
        "nudge_schedule_6_to_8_weeks",
        "Nudge schedule spans 6-8 weeks, weighted to weeks 2-6.",
        "major",
    ),
    CheckItem(
        "manager_artifacts",
        "Manager-facing artifacts present. 'What to ask in your 1:1' prompts at minimum.",
        "major",
    ),
    CheckItem(
        "relapse_prevention",
        "Final session includes relapse prevention. Named obstacles + pre-commitments fed into nudge content.",
        "minor",
    ),
    CheckItem(
        "behavior_focused_assessment",
        "Pre/post assessment is behavior-focused. Did they do X, not did they feel confident about X.",
        "major",
    ),
    CheckItem(
        "swap_test",
        "Passes the swap test. Swap 'MEDDIC' for 'Challenger' — does the program still make sense? If yes, it's slop.",
        "major",
    ),
]


# ============================================================================
# Helper functions used by validators + tests + auditor
# ============================================================================


_IMPL_INTENTION_RX = re.compile(
    r"\b(?:when|before|after|if|once)\b\s+.+?[,\s]+i('|’|’)?(\s*ll|\s+will)\s+",
    re.IGNORECASE,
)

_BANNED_VAGUE_TRIGGERS = (
    "when i have time",
    "when i get a chance",
    "whenever i remember",
    "whenever i can",
    "during the week",
    "at some point",
    "after a while",
    "before too long",
)


def has_implementation_intention(text: str) -> bool:
    """True if `text` contains a "When X, I('ll| will) Y" clause and no banned vague trigger.

    Used by the ProgramAssessment.commitment_options validator and by the
    AssessmentResponse.commitment validator to enforce Gollwitzer-shaped commitments.
    """
    if not text or not isinstance(text, str):
        return False
    lower = text.lower()
    if any(bad in lower for bad in _BANNED_VAGUE_TRIGGERS):
        return False
    return bool(_IMPL_INTENTION_RX.search(text))


def count_specifics(text: str, specifics: list[str]) -> int:
    """Count how many strings from `specifics` appear in `text` (case-insensitive).

    Used by the DesignDoc.full_markdown validator to enforce ≥3 references to
    research-derived specifics (vertical_vocab, named_competitors, customer_voice).
    """
    if not text:
        return 0
    lower = text.lower()
    count = 0
    seen: set[str] = set()
    for s in specifics:
        if not s:
            continue
        key = s.lower().strip()
        if not key or key in seen:
            continue
        if key in lower:
            count += 1
            seen.add(key)
    return count


def swap_test(text: str, behavior_token: str, swap_token: str) -> bool:
    """Returns True if literal substitution leaves the text unchanged at the
    surface (i.e., the original didn't reference behavior_token at all → slop
    risk), OR if substitution produces text that's semantically equivalent.

    For the test we use the simpler operational form: if `behavior_token` does
    not appear in `text`, the content has no grip on the behavior and IS slop —
    return True. If `behavior_token` does appear, return False (the swap will
    visibly change the text, which means it had grip).

    This is intentionally a coarse signal; combine with `count_specifics` for
    full anti-slop coverage.
    """
    if not text:
        return True
    return behavior_token.lower() not in text.lower()


_BANNED_ACTIVITY_PHRASES = (
    "discuss this",
    "share your thoughts",
    "talk about this in pairs",
    "discuss in pairs",
    "share an experience",
)


def has_banned_activity_phrase(text: str) -> bool:
    """True if `text` contains a banned generic activity phrase (forbidden for
    activity-layout slide prompts)."""
    if not text:
        return False
    lower = text.lower()
    return any(bad in lower for bad in _BANNED_ACTIVITY_PHRASES)
