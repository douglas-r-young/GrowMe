"""export_pptx writes a valid pptx with one slide per Slide."""
from pathlib import Path

from growme.decks.pptx import export_pptx
from growme.schemas import SessionDeck, Slide


def _deck() -> SessionDeck:
    return SessionDeck(
        title="Photon DB · PIC Mastery",
        behavior_ids=["a", "b", "c"],
        slides=[
            Slide(title="Welcome", body_md="x", kind="title"),
            Slide(title="Pre QR", body_md="scan", kind="poll_qr",
                  qr_url="http://localhost:8501/?assessment=u&kind=pre",
                  qr_caption="cap"),
            Slide(title="Teach", body_md="- p1\n- p2", kind="content"),
            Slide(title="Post QR", body_md="scan", kind="poll_qr",
                  qr_url="http://localhost:8501/?assessment=u&kind=post",
                  qr_caption="cap"),
            Slide(title="Close", body_md="thanks", kind="close"),
        ],
        facilitator_guide_md="# g",
        pre_qr_url="http://localhost:8501/?assessment=u&kind=pre",
        post_qr_url="http://localhost:8501/?assessment=u&kind=post",
    )


def test_export_pptx_writes_valid_pptx_with_correct_slide_count(tmp_path: Path):
    out = export_pptx(_deck(), tmp_path / "deck.pptx")
    assert out.exists()
    data = out.read_bytes()
    # PPTX is a zip; check the magic bytes.
    assert data[:2] == b"PK"

    # Verify slide count by counting slide<n>.xml entries.
    import zipfile
    with zipfile.ZipFile(out) as z:
        slide_xmls = [n for n in z.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
    assert len(slide_xmls) == 5
