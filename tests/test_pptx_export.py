"""export_pptx writes a valid pptx with one slide per Slide and notes attached."""
import zipfile
from pathlib import Path

from growme.decks.pptx import export_pptx
from growme.schemas import SessionDeck, Slide


def _slide(layout, blocks=None, **kw):
    blocks = blocks or {}
    title = blocks.get("title") or blocks.get("behavior_name") or "Untitled"
    return Slide(
        title=str(title),
        body_md=str(blocks.get("subtitle") or blocks.get("prompt") or ""),
        layout=layout,
        blocks=blocks,
        speaker_notes="Talk track for this slide. " * 8,
        **kw,
    )


def _deck() -> SessionDeck:
    return SessionDeck(
        title="Photon DB · PIC Mastery",
        behavior_ids=["a", "b", "c"],
        slides=[
            _slide("cover", {"eyebrow": "GrowMe", "title": "Welcome", "subtitle": "lo"}),
            _slide("poll_qr", {"title": "Pre QR", "body": "scan", "caption": "cap"},
                   kind="poll_qr",
                   qr_url="http://localhost:8501/?assessment=u&kind=pre",
                   qr_caption="cap"),
            _slide("section_divider", {"number": "01", "behavior_name": "Quantify pain", "promise": "p"}),
            _slide("teach", {"eyebrow": "SPIN", "title": "Quantify pain",
                             "bullets": ["a", "b", "c"], "citation": "src"}),
            _slide("example", {"title": "Before/After",
                               "before_body": "before", "after_body": "after"}),
            _slide("activity", {"eyebrow": "Try it · 5 min", "title": "Practice",
                                "prompt": "do this", "sub_prompts": ["x", "y"],
                                "timer_hint": "5 min"}),
            _slide("poll_qr", {"title": "Post QR", "body": "scan", "caption": "cap"},
                   kind="poll_qr",
                   qr_url="http://localhost:8501/?assessment=u&kind=post",
                   qr_caption="cap"),
            _slide("close", {"title": "Thanks",
                             "commitment_recap": "you committed",
                             "next_step": "nudge next week"},
                   kind="close"),
        ],
        facilitator_guide_md="# g",
        pre_qr_url="http://localhost:8501/?assessment=u&kind=pre",
        post_qr_url="http://localhost:8501/?assessment=u&kind=post",
    )


def test_export_pptx_writes_valid_pptx_with_correct_slide_count(tmp_path: Path):
    out = export_pptx(_deck(), tmp_path / "deck.pptx")
    assert out.exists()
    assert out.read_bytes()[:2] == b"PK"

    with zipfile.ZipFile(out) as z:
        names = z.namelist()
        slide_xmls = [n for n in names if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
        notes_xmls = [n for n in names if n.startswith("ppt/notesSlides/notesSlide") and n.endswith(".xml")]
    assert len(slide_xmls) == 8
    # Every slide should have an attached notes slide (we set speaker_notes on each).
    assert len(notes_xmls) == 8
