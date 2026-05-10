"""Render a SessionDeck to a 16:9 .pptx file with editorial layouts.

All layouts are built programmatically with python-pptx primitives — no master
template binary needed. Slides are fully editable in PowerPoint / Keynote.
"""
from __future__ import annotations

import io
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

from growme.qr import generate_qr_png
from growme.schemas import SessionDeck, Slide

# ---- Brand tokens ----
BRAND = RGBColor(0x2E, 0x5B, 0xFF)
INK = RGBColor(0x0F, 0x17, 0x2A)        # near-black body text
MUTED = RGBColor(0x6A, 0x73, 0x7D)
HAIRLINE = RGBColor(0xE5, 0xE7, 0xEB)
GHOST_NUM = RGBColor(0xEE, 0xF1, 0xF6)  # giant section-divider numerals

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def export_pptx(deck: SessionDeck, out_path: Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    blank = prs.slide_layouts[6]

    total = len(deck.slides)
    for idx, s in enumerate(deck.slides, start=1):
        slide = prs.slides.add_slide(blank)
        _render_slide(slide, s, deck_title=deck.title, slide_number=idx, total=total)
        if s.speaker_notes:
            slide.notes_slide.notes_text_frame.text = s.speaker_notes

    prs.save(str(out_path))
    deck.pptx_path = str(out_path)
    return out_path


# ============================================================
# Layout dispatch
# ============================================================

def _render_slide(slide, s: Slide, *, deck_title: str, slide_number: int, total: int) -> None:
    layout = s.layout
    if layout == "cover":
        _render_cover(slide, s)
    elif layout == "section_divider":
        _render_section_divider(slide, s)
    elif layout == "teach":
        _render_teach(slide, s)
    elif layout == "example":
        _render_example(slide, s)
    elif layout == "activity":
        _render_activity(slide, s)
    elif layout == "stat":
        _render_stat(slide, s)
    elif layout == "poll_qr":
        _render_poll_qr(slide, s)
    elif layout == "close":
        _render_close(slide, s)
    else:
        _render_teach(slide, s)  # safe fallback

    # Cover and section_divider are full-bleed — skip the chrome.
    if layout not in ("cover", "section_divider"):
        _add_footer(slide, deck_title, slide_number, total)


# ============================================================
# Layouts
# ============================================================

def _render_cover(slide, s: Slide) -> None:
    eyebrow = _b(s, "eyebrow", "GrowMe · Behavior change")
    title = _b(s, "title", s.title)
    subtitle = _b(s, "subtitle", s.body_md)

    # Left column for type, right column for image.
    _text(slide, eyebrow, x=0.6, y=0.7, w=6.5, h=0.4,
          size=11, color=BRAND, bold=True, uppercase=True, tracking=True)
    _text(slide, title, x=0.6, y=1.2, w=7.0, h=3.5,
          size=54, color=INK, bold=True, leading=1.05)
    _text(slide, subtitle, x=0.6, y=4.9, w=7.0, h=1.8,
          size=18, color=MUTED, leading=1.35)
    _accent_bar(slide, x=0.6, y=6.6, w=1.2)

    # Hero image on the right 40%, full-bleed top-to-bottom.
    if s.image_path and Path(s.image_path).exists():
        slide.shapes.add_picture(s.image_path, Inches(8.0), Inches(0), height=SLIDE_H)
    else:
        _placeholder_swatch(slide, x=8.0, y=0, w=5.333, h=7.5)


def _render_section_divider(slide, s: Slide) -> None:
    number = _b(s, "number", "")
    behavior_name = _b(s, "behavior_name", s.title)
    promise = _b(s, "promise", s.body_md)

    # Image left 45% full-bleed (or swatch fallback).
    if s.image_path and Path(s.image_path).exists():
        slide.shapes.add_picture(s.image_path, Inches(0), Inches(0), width=Inches(6.0), height=SLIDE_H)
    else:
        _placeholder_swatch(slide, x=0, y=0, w=6.0, h=7.5)

    # Right column: ghost numeral + behavior name + promise.
    if number:
        _text(slide, number, x=6.4, y=0.4, w=6.6, h=4.0,
              size=220, color=GHOST_NUM, bold=True, leading=0.95)
    _text(slide, behavior_name, x=6.4, y=3.6, w=6.6, h=1.8,
          size=40, color=INK, bold=True, leading=1.1)
    _accent_bar(slide, x=6.4, y=5.3, w=1.0)
    _text(slide, promise, x=6.4, y=5.5, w=6.6, h=1.6,
          size=18, color=MUTED, leading=1.4)


def _render_teach(slide, s: Slide) -> None:
    eyebrow = _b(s, "eyebrow", "Teach")
    title = _b(s, "title", s.title)
    bullets = _b(s, "bullets", []) or []
    citation = _b(s, "citation", "")

    _text(slide, eyebrow, x=0.7, y=0.7, w=12.0, h=0.4,
          size=11, color=BRAND, bold=True, uppercase=True, tracking=True)
    _text(slide, title, x=0.7, y=1.15, w=12.0, h=1.2,
          size=34, color=INK, bold=True, leading=1.1)
    _accent_bar(slide, x=0.7, y=2.35, w=0.8)

    if isinstance(bullets, list) and bullets:
        _bullet_block(slide, bullets, x=0.7, y=2.7, w=12.0, h=4.0,
                      size=20, color=INK, leading=1.4)
    elif s.body_md:
        _text(slide, s.body_md, x=0.7, y=2.7, w=12.0, h=4.0,
              size=20, color=INK, leading=1.4)

    if citation:
        _text(slide, citation, x=0.7, y=6.55, w=12.0, h=0.35,
              size=10, color=MUTED, italic=True)


def _render_example(slide, s: Slide) -> None:
    eyebrow = _b(s, "eyebrow", "Example")
    title = _b(s, "title", s.title)
    before_label = _b(s, "before_label", "Before")
    before_body = _b(s, "before_body", "")
    after_label = _b(s, "after_label", "After")
    after_body = _b(s, "after_body", "")
    pull_quote = _b(s, "pull_quote", "")

    _text(slide, eyebrow, x=0.7, y=0.7, w=12.0, h=0.4,
          size=11, color=BRAND, bold=True, uppercase=True, tracking=True)
    _text(slide, title, x=0.7, y=1.15, w=12.0, h=1.2,
          size=32, color=INK, bold=True, leading=1.1)
    _accent_bar(slide, x=0.7, y=2.35, w=0.8)

    # Two columns
    col_w, gap = 5.95, 0.4
    left_x, right_x = 0.7, 0.7 + col_w + gap

    _text(slide, before_label, x=left_x, y=2.7, w=col_w, h=0.4,
          size=11, color=MUTED, bold=True, uppercase=True, tracking=True)
    _text(slide, before_body, x=left_x, y=3.1, w=col_w, h=2.6,
          size=16, color=INK, leading=1.4)

    _text(slide, after_label, x=right_x, y=2.7, w=col_w, h=0.4,
          size=11, color=BRAND, bold=True, uppercase=True, tracking=True)
    _text(slide, after_body, x=right_x, y=3.1, w=col_w, h=2.6,
          size=16, color=INK, leading=1.4)

    if pull_quote:
        # Pull quote bar at bottom.
        _hairline(slide, x=0.7, y=6.0, w=12.0)
        _text(slide, f"“{pull_quote}”", x=0.7, y=6.1, w=12.0, h=0.7,
              size=13, color=MUTED, italic=True)


def _render_activity(slide, s: Slide) -> None:
    eyebrow = _b(s, "eyebrow", "Try it")
    title = _b(s, "title", s.title)
    prompt = _b(s, "prompt", s.body_md)
    sub_prompts = _b(s, "sub_prompts", []) or []
    timer_hint = _b(s, "timer_hint", "")

    _text(slide, eyebrow, x=0.7, y=0.7, w=12.0, h=0.4,
          size=11, color=BRAND, bold=True, uppercase=True, tracking=True)
    _text(slide, title, x=0.7, y=1.15, w=12.0, h=1.2,
          size=32, color=INK, bold=True, leading=1.1)
    _accent_bar(slide, x=0.7, y=2.35, w=0.8)

    # Brand-tinted card with the prompt + sub-prompts.
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                  Inches(0.7), Inches(2.7), Inches(12.0), Inches(3.7))
    card.fill.solid()
    card.fill.fore_color.rgb = RGBColor(0xF5, 0xF7, 0xFF)
    card.line.color.rgb = RGBColor(0xDC, 0xE3, 0xFF)

    _text(slide, prompt, x=1.0, y=2.95, w=11.4, h=1.4,
          size=22, color=INK, bold=True, leading=1.3)
    if isinstance(sub_prompts, list) and sub_prompts:
        _bullet_block(slide, sub_prompts, x=1.0, y=4.4, w=11.4, h=1.9,
                      size=15, color=INK, leading=1.4)

    if timer_hint:
        _text(slide, timer_hint, x=0.7, y=6.55, w=12.0, h=0.35,
              size=10, color=MUTED, italic=True)


def _render_stat(slide, s: Slide) -> None:
    stat_value = _b(s, "stat_value", "")
    stat_label = _b(s, "stat_label", s.title)
    source = _b(s, "source", "")

    _text(slide, stat_value, x=0.7, y=1.5, w=12.0, h=4.0,
          size=180, color=BRAND, bold=True, leading=1.0, align="left")
    _accent_bar(slide, x=0.7, y=5.7, w=1.0)
    _text(slide, stat_label, x=0.7, y=5.9, w=12.0, h=1.0,
          size=22, color=INK, leading=1.3)
    if source:
        _text(slide, source, x=0.7, y=6.85, w=12.0, h=0.3,
              size=10, color=MUTED, italic=True)


def _render_poll_qr(slide, s: Slide) -> None:
    title = _b(s, "title", s.title) or s.title
    body = _b(s, "body", s.body_md) or s.body_md
    caption = _b(s, "caption", s.qr_caption or "")

    _text(slide, "Take 60 seconds", x=0.7, y=0.7, w=8.0, h=0.4,
          size=11, color=BRAND, bold=True, uppercase=True, tracking=True)
    _text(slide, title, x=0.7, y=1.15, w=8.0, h=1.4,
          size=34, color=INK, bold=True, leading=1.1)
    _accent_bar(slide, x=0.7, y=2.6, w=0.8)
    _text(slide, body, x=0.7, y=2.9, w=8.0, h=3.5,
          size=18, color=INK, leading=1.4)

    if s.qr_url:
        png_bytes = generate_qr_png(s.qr_url)
        slide.shapes.add_picture(io.BytesIO(png_bytes),
                                 Inches(9.4), Inches(1.7),
                                 width=Inches(3.3), height=Inches(3.3))
        if caption:
            _text(slide, caption, x=9.0, y=5.15, w=4.1, h=0.6,
                  size=11, color=MUTED, italic=True, align="center")


def _render_close(slide, s: Slide) -> None:
    title = _b(s, "title", s.title)
    commitment = _b(s, "commitment_recap", s.body_md)
    next_step = _b(s, "next_step", "")

    _text(slide, "What's next", x=0.7, y=0.7, w=12.0, h=0.4,
          size=11, color=BRAND, bold=True, uppercase=True, tracking=True)
    _text(slide, title, x=0.7, y=1.15, w=12.0, h=1.4,
          size=40, color=INK, bold=True, leading=1.1)
    _accent_bar(slide, x=0.7, y=2.7, w=0.8)
    _text(slide, "Your commitment", x=0.7, y=3.0, w=12.0, h=0.4,
          size=11, color=MUTED, bold=True, uppercase=True, tracking=True)
    _text(slide, commitment, x=0.7, y=3.4, w=12.0, h=1.6,
          size=20, color=INK, leading=1.35)
    _text(slide, "Next week", x=0.7, y=5.1, w=12.0, h=0.4,
          size=11, color=MUTED, bold=True, uppercase=True, tracking=True)
    _text(slide, next_step, x=0.7, y=5.5, w=12.0, h=1.4,
          size=20, color=INK, leading=1.35)


# ============================================================
# Primitives
# ============================================================

def _b(s: Slide, key: str, default):
    """Read a typed block from `s.blocks` with a fallback."""
    val = s.blocks.get(key) if s.blocks else None
    return val if val not in (None, "") else default


def _text(
    slide, text, *, x, y, w, h,
    size=14, color=INK, bold=False, italic=False,
    leading=1.2, align="left", uppercase=False, tracking=False,
):
    if text is None:
        return
    text = str(text)
    if uppercase:
        text = text.upper()
    if tracking:
        # Letter-spaced via spaces — python-pptx has no character-spacing API on runs
        # for arbitrary kerning; emulating with thin spaces works visually.
        text = " ".join(list(text)) if len(text) <= 32 else text

    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)

    p = tf.paragraphs[0]
    p.alignment = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}[align]
    p.line_spacing = leading
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color


def _bullet_block(slide, items, *, x, y, w, h, size, color, leading):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Emu(0)
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = leading
        p.space_after = Pt(6)
        p.alignment = PP_ALIGN.LEFT
        run = p.add_run()
        run.text = f"•  {item}"
        run.font.size = Pt(size)
        run.font.color.rgb = color


def _accent_bar(slide, *, x, y, w, h=0.06):
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                 Inches(x), Inches(y), Inches(w), Inches(h))
    bar.fill.solid()
    bar.fill.fore_color.rgb = BRAND
    bar.line.fill.background()


def _hairline(slide, *, x, y, w):
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                 Inches(x), Inches(y), Inches(w), Inches(0.012))
    bar.fill.solid()
    bar.fill.fore_color.rgb = HAIRLINE
    bar.line.fill.background()


def _placeholder_swatch(slide, *, x, y, w, h):
    sw = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                Inches(x), Inches(y), Inches(w), Inches(h))
    sw.fill.solid()
    sw.fill.fore_color.rgb = RGBColor(0xF5, 0xF7, 0xFF)
    sw.line.fill.background()


def _add_footer(slide, deck_title: str, slide_number: int, total: int) -> None:
    _hairline(slide, x=0.7, y=7.05, w=11.93)
    _text(slide, deck_title, x=0.7, y=7.12, w=10.0, h=0.3,
          size=9, color=MUTED)
    _text(slide, f"{slide_number} / {total}", x=11.5, y=7.12, w=1.13, h=0.3,
          size=9, color=MUTED, align="right")
