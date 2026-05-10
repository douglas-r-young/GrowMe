"""Compose a SessionDeck from a planner-produced DeckPlan + the QR URLs.

The planner emits 18 PlannedSlide entries (cover, pre-QR, why, then 3×{divider,
teach, example, activity}, integration activity, post-QR, close). This module
turns that into a SessionDeck, overwriting the QR slide bodies with the real
URLs (planner doesn't know URLs) and attaching cached image paths to the
cover + section_divider slides.
"""
from __future__ import annotations

from pathlib import Path

from growme.decks.layouts import LAYOUTS_WITH_IMAGES
from growme.decks.llm import DeckPlan
from growme.schemas import (
    EnrichedContext,
    SessionDeck,
    SessionPlan,
    Slide,
)


def build_deck(
    *,
    plan: SessionPlan,
    enriched: EnrichedContext,
    deck_plan: DeckPlan,
    pre_qr_url: str,
    post_qr_url: str,
    facilitator_guide_md: str,
    image_paths: list[Path | None] | None = None,
    company_alias: str = "",
) -> SessionDeck:
    """Pure function. Composes the slide list. No LLM calls.

    `image_paths` is positionally aligned with the planner-emitted slides that
    declared an `image_prompt` (cover + 3 section dividers in that order).
    """
    if len(enriched.per_behavior) != 3:
        raise ValueError(
            f"enriched.per_behavior must be length 3, got {len(enriched.per_behavior)}"
        )

    title_text = plan.title or (
        f"{company_alias} · Behavior Change" if company_alias else "Behavior Change"
    )

    image_iter = iter(image_paths or [])
    seen_qr = 0
    slides: list[Slide] = []

    for ps in deck_plan.slides:
        layout = ps.layout
        blocks = dict(ps.blocks or {})

        # Overwrite the QR slide content with the canonical URLs/captions.
        # The planner produces a placeholder; we own the URLs.
        if layout == "poll_qr":
            seen_qr += 1
            is_pre = seen_qr == 1
            qr_url = pre_qr_url if is_pre else post_qr_url
            qr_caption = (
                "Scan to take the pre-program assessment"
                if is_pre else
                "Scan to take the post-program assessment + log your commitment"
            )
            blocks.setdefault("title",
                              "Pre-program assessment" if is_pre else "Post-program assessment")
            blocks.setdefault("body",
                              "Scan to take the pre-program assessment before we start."
                              if is_pre else
                              "Scan to take the post-program assessment and log your 7-day commitment.")
            blocks["caption"] = qr_caption

            slide = Slide(
                title=str(blocks.get("title", "")),
                body_md=str(blocks.get("body", "")),
                kind="poll_qr",
                qr_url=qr_url,
                qr_caption=qr_caption,
                layout="poll_qr",
                blocks=blocks,
                speaker_notes=ps.speaker_notes,
            )
            slides.append(slide)
            continue

        # Title is derived from the layout's natural title block.
        title_for_slide = (
            blocks.get("title") or blocks.get("behavior_name") or blocks.get("stat_label") or ""
        )

        image_path: str | None = None
        if layout in LAYOUTS_WITH_IMAGES:
            try:
                p = next(image_iter)
                image_path = str(p) if p is not None else None
            except StopIteration:
                image_path = None

        kind_compat = (
            "title" if layout == "cover"
            else "close" if layout == "close"
            else "content"
        )

        slides.append(Slide(
            title=str(title_for_slide),
            body_md=str(blocks.get("subtitle") or blocks.get("promise") or blocks.get("prompt") or ""),
            kind=kind_compat,
            layout=layout,
            blocks=blocks,
            speaker_notes=ps.speaker_notes,
            image_path=image_path,
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


def collect_image_prompts(deck_plan: DeckPlan) -> list[str]:
    """Pull image_prompt strings from cover + section_divider slides, in order."""
    prompts: list[str] = []
    for ps in deck_plan.slides:
        if ps.layout in LAYOUTS_WITH_IMAGES:
            p = (ps.blocks or {}).get("image_prompt", "")
            prompts.append(str(p))
    return prompts
