"""LLM auditor pass — grades a generated DeckPlan against the per-session
anti-slop checklist (pedagogy v3 doc §10).

Phase γ. Runs ONE cheap Featherless 70B call after `plan_deck` returns. The
auditor's system prompt is the per-session checklist verbatim; output is a
structured AuditReport with grade + failed_checks + suggestions.

Used by `decks.llm.plan_deck_audited` to decide whether to regenerate the deck
once with audit feedback. If still failing after one regen, the wizard shows a
yellow banner listing the failed_checks so Linda can manually fix in the deck
preview — Phase γ doesn't block the demo.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from growme.llm_clients import complete_json
from growme.pedagogy.checklist import PER_SESSION_CHECKS
from growme.schemas import EnrichedContext, SessionPlan


class FailedCheck(BaseModel):
    check_id: str
    severity: Literal["minor", "major"]
    slide_index: int | None = None
    explanation: str = Field(min_length=10)


class AuditReport(BaseModel):
    overall_grade: Literal["pass", "needs_revision", "fail"]
    failed_checks: list[FailedCheck] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list, max_length=5)


def _format_checklist() -> str:
    return "\n".join(
        f"- {c.check_id} ({c.severity}): {c.description}"
        for c in PER_SESSION_CHECKS
    )


_AUDITOR_SYSTEM = f"""\
You audit a generated training deck plan against the GrowMe per-session anti-slop
checklist (pedagogy v3 doc §10). For each check below, decide whether the deck
plan satisfies it. If the deck has multiple major failures, return overall_grade
= "needs_revision" so the planner can regenerate once. Use "fail" only for
catastrophically broken plans (no slides, no behavior coverage). Use "pass" when
no major checks fail and ≤2 minor checks fail.

CHECKLIST:
{_format_checklist()}

For each FAILED check (skip the passing ones), emit one FailedCheck with:
  - check_id: from the list above
  - severity: "minor" or "major" (use the severity from the list)
  - slide_index: the offending slide's index (1-based) if check is slide-specific,
    else null
  - explanation: ONE sentence naming what's missing or wrong, grounded in the
    actual slide content you read.

Also emit up to 5 suggestions: concrete one-line rewrites the planner could use
to fix the failed checks on the next pass.

Output strict JSON: {{ "overall_grade": ..., "failed_checks": [...], "suggestions": [...] }}.
"""


def audit_deck_plan(deck_plan, enriched: EnrichedContext, plan: SessionPlan) -> AuditReport:
    """Single LLM call. Returns the audit report.

    `deck_plan` is a DeckPlan (typed loosely here to avoid circular imports —
    `decks.llm` imports from this module via the `plan_deck_audited` orchestrator).
    """
    slides_blob = []
    for i, s in enumerate(deck_plan.slides, start=1):
        title = s.blocks.get("title") or s.blocks.get("behavior_name") or s.layout
        slides_blob.append(
            f"--- slide {i} (layout={s.layout}) — {title}\n"
            f"blocks: {s.blocks!r}\n"
            f"speaker_notes (first 240 chars): {s.speaker_notes[:240]}\n"
        )
    user = (
        f"SESSION TITLE: {plan.title}\n"
        f"LEARNING OBJECTIVE: {plan.learning_objective}\n\n"
        f"AGENDA:\n"
        + "\n".join(
            f"- {b.name} ({b.duration_min}m, bucket={b.bucket}): {b.description}"
            for b in plan.agenda
        )
        + "\n\nCOMPANY SNAPSHOT: " + enriched.base.company_snapshot
        + "\n\nDECK PLAN:\n" + "\n".join(slides_blob)
    )
    return complete_json(
        role="deck_auditor",
        system=_AUDITOR_SYSTEM,
        user=user,
        schema=AuditReport,
        max_tokens=2000,
    )


def render_audit_summary_md(report: AuditReport) -> str:
    """Format an AuditReport for display in the Streamlit banner."""
    if report.overall_grade == "pass" and not report.failed_checks:
        return "✅ Anti-slop audit passed."
    lines = [f"⚠️ Anti-slop audit grade: **{report.overall_grade}**"]
    if report.failed_checks:
        lines.append("")
        lines.append("Failed checks:")
        for fc in report.failed_checks:
            slide_ref = f" (slide {fc.slide_index})" if fc.slide_index else ""
            lines.append(f"- **{fc.check_id}** [{fc.severity}]{slide_ref}: {fc.explanation}")
    if report.suggestions:
        lines.append("")
        lines.append("Suggestions:")
        for s in report.suggestions:
            lines.append(f"- {s}")
    return "\n".join(lines)
