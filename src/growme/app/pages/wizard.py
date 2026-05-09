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
        _step_behaviors()
    elif step == 2:
        _step_generate_and_edit()
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


def _step_behaviors():
    from growme.behavior_menu import BEHAVIOR_MENU, default_pic_behavior_ids

    st.subheader("Step 2 — Pick exactly 3 behaviors")
    saved = state.get("selected_behavior_ids", default_pic_behavior_ids())

    selected: list[str] = []
    for bid, tmpl in BEHAVIOR_MENU.items():
        checked = st.checkbox(
            f"**{tmpl.name}** — _{tmpl.framework_origin}_",
            value=(bid in saved),
            help=tmpl.description,
            key=f"beh_{bid}",
        )
        if checked:
            selected.append(bid)

    st.divider()
    st.caption(f"Selected: {len(selected)} / 3")

    col_back, col_next = st.columns(2)
    if col_back.button("← Back"):
        _go_to(0)
        st.rerun()

    next_disabled = len(selected) != 3
    if col_next.button("Next →", type="primary", disabled=next_disabled):
        state.update("selected_behavior_ids", selected)
        _go_to(2)
        st.rerun()


def _step_generate_and_edit():
    from growme.design_doc.node import run as run_design_doc
    from growme.research.node import run as run_research
    from growme.schemas import WizardInputs

    st.subheader("Step 3 — Generate + Edit Design Doc")

    cached_doc = state.get("design_doc")

    if cached_doc is None:
        if st.button("🪄 Generate", type="primary"):
            inputs = WizardInputs(
                company_url=state.get("company_url"),
                company_alias=state.get("company_alias"),
                audience_description=state.get("audience_description"),
                selected_behavior_ids=state.get("selected_behavior_ids"),
            )
            with st.status("Researching...", expanded=True) as s:
                s.write("Phase A: company snapshot, customer voice, vocab, competitors...")
                s.write("Phase B: per-behavior research × 3 (parallel)...")
                enriched = run_research(inputs)
                s.write(f"Done — {len(enriched.sources_used)} sources cited.")
                s.update(label="Generating design doc...")
                doc = run_design_doc(enriched, inputs)
                s.update(label="Done.", state="complete")
            state.update("enriched_context", enriched)
            state.update("design_doc", doc)
            state.update("design_doc_edited_md", doc.full_markdown)
            st.rerun()
        return

    edited = st.text_area(
        "Design doc (editable)",
        value=state.get("design_doc_edited_md", cached_doc.full_markdown),
        height=600,
    )
    state.update("design_doc_edited_md", edited)

    col_back, col_build = st.columns(2)
    if col_back.button("← Back"):
        _go_to(1)
        st.rerun()
    if col_build.button("🚀 Build", type="primary"):
        _go_to(3)
        st.rerun()
