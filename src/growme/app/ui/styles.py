"""Global Streamlit theme: warm background, serif headings, panel styling."""

from __future__ import annotations

import streamlit as st

GLOBAL_CSS = """
<style>
@import url("https://fonts.googleapis.com/css2?family=Lora:wght@500;600;700&family=Source+Sans+3:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap");
:root {
  --growme-bg: #f4f0e8;
  --growme-surface: #fdfcfa;
  --growme-ink: #1e2a3a;
  --growme-muted: #5c6570;
  --growme-primary: #2c3e50;
}
html, body, [data-testid="stAppViewContainer"] {
  background-color: var(--growme-bg) !important;
}
[data-testid="stAppViewContainer"] .block-container {
  padding-top: 1.5rem;
  font-family: "Source Sans 3", system-ui, -apple-system, sans-serif;
  color: var(--growme-ink);
}
[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3 {
  font-family: "Lora", Georgia, "Times New Roman", serif !important;
  color: var(--growme-ink) !important;
}
[data-testid="stSidebarContent"] {
  background-color: #ebe6dc !important;
}
.stApp button[kind="primary"] {
  background-color: var(--growme-primary) !important;
  border-color: var(--growme-primary) !important;
}
.growme-panel {
  background: var(--growme-surface);
  border: 1px solid rgba(30, 42, 58, 0.08);
  border-radius: 14px;
  padding: 1.1rem 1.25rem;
  margin-bottom: 1rem;
  box-shadow: 0 2px 10px rgba(30, 42, 58, 0.06);
}
.growme-panel h3 {
  margin: 0 0 0.65rem 0;
  font-family: "Lora", Georgia, serif;
  font-size: 1.08rem;
}
.growme-progress-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 0.35rem;
  font-size: 0.9rem;
  color: var(--growme-muted);
}
.growme-progress-bar {
  flex: 1;
  max-width: 220px;
  height: 7px;
  border-radius: 4px;
  background: #e2ddd4;
  overflow: hidden;
}
.growme-progress-fill {
  height: 100%;
  border-radius: 4px;
  background: #c4763a;
}
.growme-subtitle {
  color: var(--growme-muted);
  font-size: 1rem;
  margin: 0.15rem 0 1.1rem 0;
  line-height: 1.45;
}
.growme-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0.5rem 0 0.25rem 0;
}
.growme-pill {
  background: #ece8e0;
  border-radius: 999px;
  padding: 5px 12px;
  font-size: 0.82rem;
  color: var(--growme-muted);
}
.growme-page-title {
  font-family: "Lora", Georgia, serif;
  font-size: 2rem;
  font-weight: 600;
  color: var(--growme-ink);
  margin-bottom: 0;
}
</style>
"""


def inject_global_css() -> None:
    if st.session_state.get("_growme_global_css"):
        return
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    st.session_state["_growme_global_css"] = True
