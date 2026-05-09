"""Streamlit helpers for in-app deck preview."""
from __future__ import annotations

import streamlit as st

from growme.qr import generate_qr_png
from growme.schemas import SessionDeck


_CARD_CSS = """
<style>
.growme-slide-card {
    border: 1px solid #e1e4e8; border-radius: 8px;
    padding: 1.25rem 1.5rem; margin-bottom: 1rem;
    background: #ffffff; box-shadow: 0 1px 2px rgba(0,0,0,.04);
}
.growme-slide-card .slide-kind {
    text-transform: uppercase; font-size: 11px; letter-spacing: .08em;
    color: #6a737d; margin-bottom: .25rem;
}
.growme-slide-card h3 { margin-top: 0; margin-bottom: .5rem; }
</style>
"""


def render_deck(deck: SessionDeck) -> None:
    st.markdown(_CARD_CSS, unsafe_allow_html=True)
    for i, slide in enumerate(deck.slides, start=1):
        with st.container():
            st.markdown("<div class='growme-slide-card'>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='slide-kind'>Slide {i} — {slide.kind}</div>"
                f"<h3>{_escape(slide.title)}</h3>",
                unsafe_allow_html=True,
            )
            if slide.kind == "poll_qr" and slide.qr_url:
                left, right = st.columns([3, 2])
                with left:
                    st.markdown(slide.body_md)
                with right:
                    st.image(generate_qr_png(slide.qr_url), caption=slide.qr_caption or "")
            else:
                st.markdown(slide.body_md)
            st.markdown("</div>", unsafe_allow_html=True)


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
