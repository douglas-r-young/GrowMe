# src/growme/app/pages/wizard.py
"""4-step wizard. Persists inputs across reruns via state.py."""
from __future__ import annotations

import streamlit as st

from growme.app import state


STEPS = ["Company + Audience", "Behaviors", "Generate + Edit", "Build"]


def _current_step() -> int:
    return st.session_state.setdefault("wizard_step", 0)


def _go_to(step: int) -> None:
    st.session_state["wizard_step"] = max(0, min(len(STEPS) - 1, step))


def render():
    st.title("GrowMe Wizard")

    step = _current_step()
    cols = st.columns(len(STEPS))
    for i, label in enumerate(STEPS):
        cols[i].markdown(f"**{i+1}. {label}**" if i == step else f"{i+1}. {label}")

    st.divider()

    if step == 0:
        _step_company_audience()
    elif step == 1:
        st.warning("Step 2 not implemented yet — see Task 12.")
    elif step == 2:
        st.warning("Step 3 not implemented yet — see Task 17 / 18.")
    elif step == 3:
        st.warning("Step 4 not implemented yet — see Task 25.")


def _step_company_audience():
    saved_url = state.get("company_url", "neon.tech")
    saved_alias = state.get("company_alias", "Photon DB")
    saved_audience = state.get(
        "audience_description",
        "12 mid-market AEs, 1-3 yrs tenure, expanding into healthcare",
    )

    st.subheader("Step 1 — Company + Audience")
    company_url = st.text_input(
        "Company URL (real, used by research)",
        value=saved_url,
        help="The Apify crawler will hit this URL.",
    )
    company_alias = st.text_input(
        "Company alias (shown in all output)",
        value=saved_alias,
        help="The output will use this name. Real name gets find/replace before display.",
    )
    audience_description = st.text_area(
        "Audience description",
        value=saved_audience,
        height=120,
        help="Short paragraph describing the cohort.",
    )

    if st.button("Next →", type="primary"):
        state.update("company_url", company_url.strip())
        state.update("company_alias", company_alias.strip())
        state.update("audience_description", audience_description.strip())
        _go_to(1)
        st.rerun()
