"""LLM calls that fill in slide bodies + the facilitator guide."""
from __future__ import annotations

from pydantic import BaseModel, Field

from growme.llm_clients import complete_json
from growme.schemas import EnrichedContext, SessionPlan, WizardInputs


class _SlideBody(BaseModel):
    title: str
    body_md: str = Field(min_length=20)


class _SlideBundle(BaseModel):
    slides: list[_SlideBody] = Field(min_length=4, max_length=4)


SLIDES_SYSTEM = """\
You are an instructional designer. Produce 4 content slides for a 60-minute training session
that integrates THREE behaviors. Required order:
  1. Behavior #1 teach — 2-4 bullet points sourced from the findings (examples + baselines)
  2. Behavior #2 teach — same shape
  3. Behavior #3 teach — same shape
  4. Integration teach — how the three behaviors compose into one deal motion
Use markdown bullets in body_md. Keep each slide under 80 words.
Output strict JSON: { "slides": [Slide, Slide, Slide, Slide] }.
"""


class _Guide(BaseModel):
    full_markdown: str = Field(min_length=200)


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
Output strict JSON: { "full_markdown": "..." }.
"""


def gen_slide_bodies(plan: SessionPlan, enriched: EnrichedContext) -> list[tuple[str, str]]:
    """Returns 4 (title, body_md) tuples in canonical order: B1, B2, B3, Integration."""
    behavior_blob = "\n\n---\n\n".join(_format_behavior(bc) for bc in enriched.per_behavior)
    user = (
        f"SESSION: {plan.title}\nLEARNING OBJECTIVE: {plan.learning_objective}\n\n"
        f"FINDINGS:\n{behavior_blob}\n"
    )
    bundle = complete_json(role="materials", system=SLIDES_SYSTEM, user=user, schema=_SlideBundle)
    return [(s.title, s.body_md) for s in bundle.slides]


def gen_facilitator_guide(plan: SessionPlan, enriched: EnrichedContext) -> str:
    """Returns the full guide markdown."""
    behavior_blob = "\n\n---\n\n".join(_format_behavior(bc) for bc in enriched.per_behavior)
    user = (
        f"SESSION: {plan.title}\nLEARNING OBJECTIVE: {plan.learning_objective}\n\n"
        f"AGENDA:\n" + "\n".join(f"- {a.name} ({a.duration_min}m): {a.description}" for a in plan.agenda)
        + "\n\nFINDINGS:\n" + behavior_blob
    )
    g = complete_json(role="materials", system=GUIDE_SYSTEM, user=user, schema=_Guide,
                      max_tokens=3000)
    return g.full_markdown


def _format_behavior(bc) -> str:
    def fmt(label, items):
        if not items:
            return f"{label}: (none)"
        return f"{label}:\n" + "\n".join(f"- {f.text}" for f in items[:5])
    return (
        f"BEHAVIOR: {bc.behavior_name} ({bc.framework_origin})\n"
        f"DESCRIPTION: {bc.behavior_description}\n\n"
        f"{fmt('EXAMPLES', bc.findings.examples)}\n\n"
        f"{fmt('BASELINES', bc.findings.baselines)}\n\n"
        f"{fmt('OBJECTIONS', bc.findings.objections)}\n\n"
        f"{fmt('PROOF_POINTS', bc.findings.proof_points)}\n"
    )
