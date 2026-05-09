"""Export a SessionDeck to a .pptx file using python-pptx.

QR slides embed the QR PNG generated via growme.qr.
"""
from __future__ import annotations

import io
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

from growme.qr import generate_qr_png
from growme.schemas import SessionDeck, Slide

BRAND_RGB = RGBColor(0x2E, 0x5B, 0xFF)
FOOTER_RGB = RGBColor(0x6A, 0x73, 0x7D)


def export_pptx(deck: SessionDeck, out_path: Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    prs = Presentation()
    blank = prs.slide_layouts[6]
    total = len(deck.slides)
    footer_text = f"{deck.title} · Session {deck.session_number} of {total}"

    for s in deck.slides:
        slide = prs.slides.add_slide(blank)
        _add_title(slide, s.title)
        if s.kind == "poll_qr" and s.qr_url:
            _add_qr_layout(slide, s)
        else:
            _add_text_block(slide, s.body_md)
        _add_accent(slide)
        _add_footer(slide, footer_text)

    prs.save(str(out_path))
    deck.pptx_path = str(out_path)
    return out_path


def _add_title(slide, text: str) -> None:
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(1))
    p = tb.text_frame.paragraphs[0]
    p.text = text
    p.runs[0].font.size = Pt(32)
    p.runs[0].font.bold = True
    p.runs[0].font.color.rgb = BRAND_RGB


def _add_text_block(slide, body_md: str) -> None:
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(9), Inches(5))
    tf = tb.text_frame
    tf.word_wrap = True
    lines = body_md.split("\n")
    first = True
    for line in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.text = line
        for run in p.runs:
            run.font.size = Pt(18)


def _add_qr_layout(slide, s: Slide) -> None:
    # Body markdown on the left, QR image on the right.
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(5.5), Inches(5))
    tf = tb.text_frame
    tf.word_wrap = True
    first = True
    for line in s.body_md.split("\n"):
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.text = line
        for run in p.runs:
            run.font.size = Pt(16)

    png_bytes = generate_qr_png(s.qr_url or "")
    image_stream = io.BytesIO(png_bytes)
    slide.shapes.add_picture(image_stream, Inches(6.5), Inches(2.0), width=Inches(2.8))

    if s.qr_caption:
        cap = slide.shapes.add_textbox(Inches(6.0), Inches(5.0), Inches(3.5), Inches(0.6))
        cap_p = cap.text_frame.paragraphs[0]
        cap_p.text = s.qr_caption
        cap_p.runs[0].font.size = Pt(12)


def _add_accent(slide) -> None:
    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(1.2), Inches(9.0), Inches(0.04)
    )
    line.fill.solid()
    line.fill.fore_color.rgb = BRAND_RGB
    line.line.fill.background()  # no border


def _add_footer(slide, footer_text: str) -> None:
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(6.9), Inches(9.0), Inches(0.4))
    p = tb.text_frame.paragraphs[0]
    p.text = footer_text
    run = p.runs[0]
    run.font.size = Pt(10)
    run.font.color.rgb = FOOTER_RGB
