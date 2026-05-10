"""LLM calls that produce a fully-planned DeckPlan + the facilitator guide.

The planner is the single source of truth for content. The renderer never invents
text — it only fills the placeholders the planner emits.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from growme.decks.layouts import LayoutKind
from growme.llm_clients import complete, complete_json
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
    before_body: str = Field(min_length=10, max_length=320)
    after_label: str = Field(default="After", max_length=24)
    after_body: str = Field(min_length=10, max_length=320)
    pull_quote: str = Field(default="", max_length=240)


class ActivityBlocks(BaseModel):
    eyebrow: str = Field(min_length=2, max_length=40)      # e.g. "Try it · 5 min"
    title: str = Field(min_length=4, max_length=80)
    prompt: str = Field(min_length=10, max_length=300)
    sub_prompts: list[str] = Field(default_factory=list, max_length=4)
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
    commitment_recap: str = Field(min_length=10, max_length=240)
    next_step: str = Field(min_length=10, max_length=240)


# Discriminated by `layout`.
class PlannedSlide(BaseModel):
    layout: LayoutKind
    blocks: dict = Field(default_factory=dict)
    speaker_notes: str = Field(min_length=80)


class DeckPlan(BaseModel):
    slides: list[PlannedSlide] = Field(min_length=14, max_length=20)


# ---------- Planner prompt ----------

PLANNER_SYSTEM = """\
You are a senior instructional designer and presentation writer for B2B sales-enablement
training. Your job: turn the session plan + per-behavior research into a deck that a
real facilitator could deliver tomorrow without rewriting a single slide.

NON-NEGOTIABLES
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

CONTENT BLOCK CONTRACTS (the keys that must appear in `blocks` for each layout):
- cover:           {eyebrow, title, subtitle, image_prompt}
- section_divider: {number, behavior_name, promise, image_prompt}
- teach:           {eyebrow, title, bullets:[...], citation}
- example:         {eyebrow, title, before_label, before_body, after_label, after_body, pull_quote}
- activity:        {eyebrow, title, prompt, sub_prompts:[...], timer_hint}
- stat:            {stat_value, stat_label, source}
- poll_qr:         {title, body, caption}
- close:           {title, commitment_recap, next_step}

Output strict JSON: { "slides": [PlannedSlide, ...] }.
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


def plan_deck(plan: SessionPlan, enriched: EnrichedContext) -> DeckPlan:
    """Single LLM call. Returns the full slide plan with content + speaker notes.

    The two QR slides come back as `poll_qr` placeholders; the URL/caption are
    overwritten downstream in builder.build_deck (the planner doesn't know URLs).
    """
    user = _skeleton_prompt(plan, enriched)
    return complete_json(
        role="deck_planner",
        system=PLANNER_SYSTEM,
        user=user,
        schema=DeckPlan,
        max_tokens=8000,
    )


# ---------- Facilitator guide ----------

GUIDE_SYSTEM = """\
You produce a markdown facilitator guide for a 60-minute single-session training that
covers three behaviors. Sections (use level-2 headings):
  ## Setup (10 min before)
  ## Opening hook (5 min)
  ## Teach (15 min)  -- include specific points + how to handle the top 1-2 objections per behavior
  ## Discuss (15 min) -- 2-3 discussion prompts touching all three behaviors
  ## Practice / Role-play (15 min) -- a multi-behavior scenario; rep must switch between behaviors
  ## Commitment + close (10 min)
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
