"""LLM calls that produce a fully-planned DeckPlan + the facilitator guide.

The planner is the single source of truth for content. The renderer never invents
text — it only fills the placeholders the planner emits.

PLANNER_SYSTEM and GUIDE_SYSTEM concatenate pedagogy bundles — the planner gets
DECK_PEDAGOGY_NON_NEGOTIABLES (story stems, calibration questions, anti-pattern
callouts, no fictional companies, stage-of-change diversity, implementation
intentions, relapse-prevention beat, human-handoff in speaker notes). The guide
gets GUIDE_FACILITATION_PRINCIPLES (wait time, story-slot fallbacks, objection
pairing, buffer enforcement).
"""
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

from growme.decks.layouts import LayoutKind
from growme.llm_clients import complete, complete_json
from growme.pedagogy import (
    DECK_PEDAGOGY_NON_NEGOTIABLES,
    GUIDE_FACILITATION_PRINCIPLES,
    MANAGER_BRIEFING_PRINCIPLES,
)
from growme.schemas import EnrichedContext, SessionPlan


# ---------- Planner schema ----------

class CoverBlocks(BaseModel):
    eyebrow: str = Field(min_length=2, max_length=40)
    title: str = Field(min_length=4, max_length=80)
    subtitle: str = Field(min_length=10, max_length=160)
    image_prompt: str = Field(min_length=20)


class SectionDividerBlocks(BaseModel):
    number: str = Field(min_length=1, max_length=4)        # "01", "02", "03"
    behavior_name: str = Field(min_length=2, max_length=60)
    promise: str = Field(min_length=10, max_length=140)
    image_prompt: str = Field(min_length=20)


class TeachBlocks(BaseModel):
    eyebrow: str = Field(min_length=2, max_length=40)      # framework name
    title: str = Field(min_length=4, max_length=80)
    bullets: list[str] = Field(min_length=2, max_length=4)
    citation: str = Field(default="", max_length=120)


class ExampleBlocks(BaseModel):
    eyebrow: str = Field(default="Example", max_length=40)
    title: str = Field(min_length=4, max_length=80)
    before_label: str = Field(default="Before", max_length=24)
    before_body: str = Field(min_length=10, max_length=260)
    after_label: str = Field(default="After", max_length=24)
    after_body: str = Field(min_length=10, max_length=260)
    pull_quote: str = Field(default="", max_length=200)


class ActivityBlocks(BaseModel):
    eyebrow: str = Field(min_length=2, max_length=40)      # e.g. "Try it · 5 min"
    title: str = Field(min_length=4, max_length=80)
    prompt: str = Field(min_length=10, max_length=180)
    sub_prompts: list[Annotated[str, Field(max_length=100)]] = Field(
        default_factory=list, max_length=4,
    )
    timer_hint: str = Field(default="", max_length=60)


class StatBlocks(BaseModel):
    stat_value: str = Field(min_length=1, max_length=12)
    stat_label: str = Field(min_length=4, max_length=140)
    source: str = Field(default="", max_length=120)


class PollQRBlocks(BaseModel):
    title: str
    body: str
    caption: str


class CloseBlocks(BaseModel):
    title: str = Field(min_length=4, max_length=80)
    commitment_recap: str = Field(min_length=10, max_length=180)
    commitment_alternates: list[str] = Field(default_factory=list, max_length=3)
    """Phase γ: 0-3 stage-tone alternates (skeptic / beginner / practitioner) the
    facilitator invites the room to pick from. Each is an "When X, I will Y"
    short variant. The renderer in pptx.py shows them under a "Or pick one that
    fits your week" sub-section if the planner emitted any."""
    next_step: str = Field(min_length=10, max_length=180)


# Discriminated by `layout`.
class PlannedSlide(BaseModel):
    layout: LayoutKind
    blocks: dict = Field(default_factory=dict)
    speaker_notes: str = Field(min_length=80)

    @model_validator(mode="after")
    def _activity_prompt_not_banned(self) -> "PlannedSlide":
        """Block generic placeholder prompts on activity slides — per pedagogy v3
        doc §10 anti-slop checklist, every activity must produce a real artifact."""
        if self.layout != "activity":
            return self
        from growme.pedagogy.checklist import has_banned_activity_phrase
        prompt = self.blocks.get("prompt", "")
        if isinstance(prompt, str) and has_banned_activity_phrase(prompt):
            raise ValueError(
                f"Activity prompt {prompt!r} matches a banned generic phrase "
                "(per pedagogy v3 anti-slop checklist). Activity prompts must give "
                "the facilitator a runnable scenario, not 'discuss this' or 'share "
                "your thoughts'."
            )
        return self


class DeckPlan(BaseModel):
    slides: list[PlannedSlide] = Field(min_length=14, max_length=20)


# ---------- Planner prompt ----------

PLANNER_SYSTEM = f"""\
You are a senior instructional designer and presentation writer for B2B sales-enablement
training. Your job: turn the session plan + per-behavior research into a deck that a
real facilitator could deliver tomorrow without rewriting a single slide.

STRUCTURAL NON-NEGOTIABLES
1. Never put the raw learning objective on a slide as body text. Translate it.
2. Every teach slide names a real framework or technique (e.g. SPIN, MEDDPICC, Challenger
   reframe, Sandler pain funnel) and gives 2-4 short, specific HOW bullets — not WHAT bullets.
3. Every example slide shows a concrete BEFORE / AFTER drawn from the research findings
   (examples + baselines). Use the company's actual customer voice when present.
4. Every activity slide gives the facilitator a runnable prompt: a real scenario, 2-3
   sub-prompts, and a "Try it · N min" eyebrow. Never "Discuss this." alone.
5. Speaker notes (>= 80 words) on EVERY slide. Notes include: the talk-track, the top
   objection a learner might raise, and how to handle it.
6. Cover + each section divider include an image_prompt (a single sentence, editorial
   abstract style — geometric, restrained, no people, no text-in-image).
7. Output exactly the slide sequence requested in the user message, in order, no extras.
8. CLOSE SLIDE: `commitment_recap` is ONE tight prose paragraph (≤180 chars) that
   summarizes the three behaviors the learner just practiced — never a bulleted list,
   never a duplicate of body slides. `next_step` is a single, specific 24-hour action
   (e.g. "Open your top open opp and rewrite your discovery notes using today's three
   behaviors before your next call"), not a 3-step list.
9. KEEP IT SHORT: every body field has a hard char cap below; if you exceed it the
   slide will be silently shrunk by the renderer. Stay inside the cap so the on-slide
   text reads at full size.

{DECK_PEDAGOGY_NON_NEGOTIABLES}

CONTENT BLOCK CONTRACTS (keys + char caps for each layout):
- cover:           eyebrow ≤40, title ≤80, subtitle ≤160, image_prompt
- section_divider: number ≤4 ("01"|"02"|"03"), behavior_name ≤60, promise ≤140, image_prompt
- teach:           eyebrow ≤40, title ≤80, bullets 2–4 items, citation ≤120
- example:         title ≤80, before_label ≤24, before_body ≤260, after_label ≤24,
                   after_body ≤260, pull_quote ≤200 (goes into speaker notes only —
                   never rendered on the slide, so write it as a clean facilitator
                   one-liner the speaker reads aloud)
- activity:        eyebrow ≤40, title ≤80, prompt ≤180, sub_prompts ≤4 items
                   (each ≤100), timer_hint ≤60
- stat:            stat_value ≤12, stat_label ≤140, source ≤120
- poll_qr:         title, body, caption
- close:           title ≤80, commitment_recap ≤180, commitment_alternates 0-3 items
                   (each ≤140 — "When X, I will Y" form, one per stage of change:
                   skeptic / beginner / practitioner), next_step ≤180

Output strict JSON: {{ "slides": [PlannedSlide, ...] }}.
"""


def _format_behavior(bc, idx: int) -> str:
    def fmt(label, items):
        if not items:
            return f"{label}: (none)"
        return f"{label}:\n" + "\n".join(f"- {f.text}  [{f.source}]" for f in items[:5])
    return (
        f"### Behavior {idx} — {bc.behavior_name} ({bc.framework_origin})\n"
        f"Description: {bc.behavior_description}\n\n"
        f"{fmt('EXAMPLES', bc.findings.examples)}\n\n"
        f"{fmt('BASELINES', bc.findings.baselines)}\n\n"
        f"{fmt('OBJECTIONS', bc.findings.objections)}\n\n"
        f"{fmt('PROOF_POINTS', bc.findings.proof_points)}\n"
    )


def _skeleton_prompt(plan: SessionPlan, enriched: EnrichedContext) -> str:
    from growme.decks.layouts import STORY_ARC_SKELETON

    lines = [
        f"SESSION TITLE: {plan.title}",
        f"LEARNING OBJECTIVE: {plan.learning_objective}",
        f"COMPANY SNAPSHOT: {enriched.base.company_snapshot}",
        "",
        "BEHAVIOR FINDINGS:",
    ]
    for i, bc in enumerate(enriched.per_behavior, start=1):
        lines.append(_format_behavior(bc, i))

    lines.append("\nPRODUCE THESE SLIDES IN THIS EXACT ORDER:")
    for i, (layout, role) in enumerate(STORY_ARC_SKELETON, start=1):
        lines.append(f"{i:>2}. layout={layout!r}  — {role}")
    return "\n".join(lines)


def plan_deck(
    plan: SessionPlan,
    enriched: EnrichedContext,
    *,
    audit_feedback: str = "",
) -> DeckPlan:
    """Single LLM call. Returns the full slide plan with content + speaker notes.

    The two QR slides come back as `poll_qr` placeholders; the URL/caption are
    overwritten downstream in builder.build_deck (the planner doesn't know URLs).

    `audit_feedback` (Phase γ): if a previous pass failed the anti-slop audit,
    pass the failed_checks summary here so the planner can correct on this pass.
    """
    user = _skeleton_prompt(plan, enriched)
    if audit_feedback:
        user += (
            "\n\nAUDIT FEEDBACK from a prior generation (fix these on this pass):\n"
            + audit_feedback
        )
    return complete_json(
        role="deck_planner",
        system=PLANNER_SYSTEM,
        user=user,
        schema=DeckPlan,
        max_tokens=8000,
    )


def plan_deck_audited(
    plan: SessionPlan,
    enriched: EnrichedContext,
    *,
    max_audit_retries: int = 1,
):
    """Plan a deck, then run the anti-slop auditor (Phase γ).

    Returns a tuple (DeckPlan, AuditReport | None). If the auditor reports
    `needs_revision` and we have retries remaining, regenerates the deck once
    with the audit feedback appended to the user prompt. If still failing,
    returns the latest deck + audit so the wizard can show a banner with the
    failed_checks. We never block the demo on audit failure.
    """
    from growme.pedagogy.auditor import AuditReport, audit_deck_plan

    deck_plan = plan_deck(plan, enriched)
    audit: AuditReport | None = None
    try:
        audit = audit_deck_plan(deck_plan, enriched, plan)
    except Exception as e:  # auditor failure must NEVER break the build
        print(f"[auditor] grade pass failed: {e}; shipping unaudited deck.")
        return deck_plan, None

    if audit.overall_grade == "needs_revision" and max_audit_retries > 0:
        feedback_lines = [
            f"- {fc.check_id}{f' (slide {fc.slide_index})' if fc.slide_index else ''}: "
            f"{fc.explanation}"
            for fc in audit.failed_checks
        ]
        feedback_lines.extend(f"- suggestion: {s}" for s in audit.suggestions)
        feedback = "\n".join(feedback_lines)
        deck_plan = plan_deck(plan, enriched, audit_feedback=feedback)
        try:
            audit = audit_deck_plan(deck_plan, enriched, plan)
        except Exception as e:
            print(f"[auditor] re-audit failed: {e}; shipping the regenerated deck.")
            audit = None
    return deck_plan, audit


# ---------- Facilitator guide ----------

GUIDE_SYSTEM = f"""\
You produce a markdown facilitator guide for a 60-minute single-session training that
covers three behaviors. Sections (use level-2 headings):
  ## Setup (10 min before)
  ## Opening hook (5 min)
  ## Teach (15 min)  -- include specific points + how to handle the top 1-2 objections per behavior
  ## Discuss (15 min) -- 2-3 discussion prompts touching all three behaviors
  ## Practice / Role-play (15 min) -- a multi-behavior scenario; rep must switch between behaviors
  ## Commitment + close (10 min)

{GUIDE_FACILITATION_PRINCIPLES}

Ground objections + scenarios in the provided behavior findings.
Reference the deck's slide titles where relevant so the facilitator knows where they are.
Output ONLY the markdown body — no JSON, no code fences, no preamble.
"""


def gen_facilitator_guide(
    plan: SessionPlan,
    enriched: EnrichedContext,
    deck_plan: DeckPlan | None = None,
) -> str:
    """Returns the full guide markdown, optionally aware of the planned slide titles."""
    behavior_blob = "\n\n---\n\n".join(_format_behavior(bc, i) for i, bc in enumerate(enriched.per_behavior, 1))
    slide_titles = ""
    if deck_plan is not None:
        titles = []
        for i, s in enumerate(deck_plan.slides, start=1):
            t = s.blocks.get("title") or s.blocks.get("behavior_name") or s.layout
            titles.append(f"{i}. ({s.layout}) {t}")
        slide_titles = "\n\nSLIDE TITLES (for cross-reference):\n" + "\n".join(titles)

    user = (
        f"SESSION: {plan.title}\nLEARNING OBJECTIVE: {plan.learning_objective}\n\n"
        f"AGENDA:\n" + "\n".join(f"- {a.name} ({a.duration_min}m): {a.description}" for a in plan.agenda)
        + "\n\nFINDINGS:\n" + behavior_blob
        + slide_titles
    )
    md = complete(role="materials", system=GUIDE_SYSTEM, user=user,
                  temperature=0.3, max_tokens=8000)
    md = md.strip()
    if md.startswith("```"):
        md = md.split("\n", 1)[1] if "\n" in md else md[3:]
        if md.endswith("```"):
            md = md[:-3]
        md = md.strip()
    if len(md) < 400:
        raise ValueError(f"facilitator guide too short ({len(md)} chars)")
    return md


# ---------- Manager 1:1 briefing (Phase β) ----------

MANAGER_BRIEFING_SYSTEM = f"""\
You produce a one-page markdown manager briefing titled "What to ask in your 1:1
over the next 6 weeks" for a sales-enablement training program. The audience
is the rep's MANAGER, not the rep. Tone: collegial, time-respecting, directly
actionable.

Required structure (use exactly these level-2 headings, in this order):
  ## Why this matters
  ## Week 1 — the launch window
  ## Week 3 — when the dip starts
  ## Week 5 — checkpoint
  ## Week 7 — sustained behavior
  ## Watch for — relapse signals
  ## What NOT to ask

Each weekly section has 2-3 specific 1:1 prompts grounded in the behaviors and
their commitments. The prompt names the behavior, the trigger, and the kind of
answer to expect (concrete, not "how confident do you feel?").

{MANAGER_BRIEFING_PRINCIPLES}

Ground prompts in the provided design-doc + per-behavior findings. Length:
600-1000 words. Output ONLY the markdown body — no JSON, no code fences,
no preamble.
"""


def gen_manager_briefing(
    plan: SessionPlan,
    enriched: EnrichedContext,
    deck_plan: DeckPlan | None,
    design_doc_md: str,
) -> str:
    """Returns the manager 1:1 briefing markdown. ~600-1000 words."""
    behavior_blob = "\n\n---\n\n".join(
        _format_behavior(bc, i) for i, bc in enumerate(enriched.per_behavior, 1)
    )
    slide_titles_blob = ""
    if deck_plan is not None:
        titles = []
        for i, s in enumerate(deck_plan.slides, start=1):
            t = s.blocks.get("title") or s.blocks.get("behavior_name") or s.layout
            titles.append(f"{i}. ({s.layout}) {t}")
        slide_titles_blob = "\n\nDECK SLIDE TITLES:\n" + "\n".join(titles)

    user = (
        f"SESSION: {plan.title}\n"
        f"LEARNING OBJECTIVE: {plan.learning_objective}\n\n"
        f"DESIGN DOC (excerpt):\n{design_doc_md[:2500]}\n\n"
        f"PER-BEHAVIOR FINDINGS:\n{behavior_blob}"
        f"{slide_titles_blob}\n"
    )
    md = complete(
        role="manager_briefing",
        system=MANAGER_BRIEFING_SYSTEM,
        user=user,
        temperature=0.3,
        max_tokens=4000,
    )
    md = md.strip()
    if md.startswith("```"):
        md = md.split("\n", 1)[1] if "\n" in md else md[3:]
        if md.endswith("```"):
            md = md[:-3]
        md = md.strip()
    if len(md) < 400:
        raise ValueError(f"manager briefing too short ({len(md)} chars)")
    return md
