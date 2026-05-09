"""Compose a SessionDeck: title + pre QR + 4 teach slides + post QR + close."""
from __future__ import annotations

from growme.schemas import (
    EnrichedContext,
    ProgramAssessment,
    SessionDeck,
    SessionPlan,
    Slide,
)


def build_deck(
    *,
    plan: SessionPlan,
    enriched: EnrichedContext,
    assessment: ProgramAssessment,
    pre_qr_url: str,
    post_qr_url: str,
    slide_bodies: list[tuple[str, str]],
    facilitator_guide_md: str,
    company_alias: str = "",
) -> SessionDeck:
    """Pure function. Composes the slide list. No LLM calls.

    `slide_bodies` is a 4-tuple list (title, body_md) for B1, B2, B3, Integration.
    `assessment` is kept in the signature for downstream use; QR slides use a
    minimal scan-CTA body so the assessment content stays in the assessment page.
    """
    if len(slide_bodies) != 4:
        raise ValueError(f"slide_bodies must be length 4, got {len(slide_bodies)}")
    if len(enriched.per_behavior) != 3:
        raise ValueError(
            f"enriched.per_behavior must be length 3, got {len(enriched.per_behavior)}"
        )
    _ = assessment  # currently used by the assessment page; kept here for symmetric Build args.

    title_text = plan.title or (f"{company_alias} · Behavior Change" if company_alias else "Behavior Change")
    pre_qr_caption = "Scan to take the pre-program assessment"
    post_qr_caption = "Scan to take the post-program assessment + log your commitment"

    slides: list[Slide] = []
    slides.append(Slide(title=title_text, body_md=plan.learning_objective, kind="title"))
    slides.append(Slide(
        title="Pre-program assessment",
        body_md="Scan to take the pre-program assessment before we start.",
        kind="poll_qr",
        qr_url=pre_qr_url,
        qr_caption=pre_qr_caption,
    ))
    for title, body in slide_bodies:
        slides.append(Slide(title=title, body_md=body, kind="content"))
    slides.append(Slide(
        title="Post-program assessment",
        body_md="Scan to take the post-program assessment and log your 7-day commitment.",
        kind="poll_qr",
        qr_url=post_qr_url,
        qr_caption=post_qr_caption,
    ))
    slides.append(Slide(
        title="Thanks — what's next",
        body_md="You'll receive a personalized nudge next week tied to your commitment.",
        kind="close",
    ))

    return SessionDeck(
        session_number=plan.session_number,
        title=title_text,
        behavior_ids=[bc.behavior_id for bc in enriched.per_behavior],
        slides=slides,
        facilitator_guide_md=facilitator_guide_md,
        pptx_path=None,
        pre_qr_url=pre_qr_url,
        post_qr_url=post_qr_url,
    )
