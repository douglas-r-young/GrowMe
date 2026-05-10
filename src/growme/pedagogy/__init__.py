"""Pedagogy package — single source of truth for the principles GrowMe operates from.

`full_context.md` holds the verbatim research-and-instructions doc (Adult Learning &
Behavior Change Context for GrowMe, working draft v0.3). Editing happens there.

`principles.py` exposes role-curated bundles as module-level string constants. Every
LLM `*_SYSTEM` prompt imports the relevant bundle and concatenates it into its
system prompt. The bundles are extracts hand-curated from `full_context.md` — not
the full doc. Curation is the work.

`checklist.py` exposes the anti-slop checklists as structured Python data plus
helper functions (`swap_test`, `count_specifics`, `has_implementation_intention`).
The structured data feeds the LLM auditor in `auditor.py`.

`auditor.py` (Phase γ) audits a generated DeckPlan against the per-session
checklist; reports pass/needs_revision/fail with actionable failed_checks.
"""
from growme.pedagogy.principles import (
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

__all__ = [
    "ANTI_SLOP_TAIL",
    "ASSESSMENT_PRINCIPLES",
    "BEHAVIOR_ALTITUDE_PRINCIPLES",
    "DECK_PEDAGOGY_NON_NEGOTIABLES",
    "DESIGN_DOC_PRINCIPLES",
    "GUIDE_FACILITATION_PRINCIPLES",
    "HUMAN_HANDOFF_PRINCIPLES",
    "IMPLEMENTATION_INTENTION_RULES",
    "MANAGER_BRIEFING_PRINCIPLES",
    "NUDGE_PRINCIPLES",
    "PACING_PRINCIPLES",
    "SESSION_PLAN_PRINCIPLES",
    "STAGE_OF_CHANGE_PRINCIPLES",
    "TRANSFER_PRINCIPLES",
]
