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
        _step_build()


_AUDIENCE_PLACEHOLDER = (
    "12 mid-market AEs, 1-3 yrs tenure. They run discovery calls but don't quantify "
    "pain in business-impact terms. The comp plan rewards velocity over qualification; "
    "reps know they should ask 'how do you measure that?' but default to capability "
    "pitch under quota pressure. Expanding into healthcare verticals where buyers "
    "expect ROI math up front."
)

_AUDIENCE_HELP = (
    "Be specific. The pedagogy doc demands behavior altitude (what would they do "
    "differently next Tuesday?) AND the resistance pattern (skill gap, habit, "
    "incentive mismatch, fear, or environment). Vague inputs = generic output. "
    "If you're not sure about the resistance pattern, write what's getting in "
    "the way today and the agent will infer."
)


def _step_company_audience():
    saved_url = state.get("company_url", "neon.tech")
    saved_alias = state.get("company_alias", "Photon DB")
    saved_audience = state.get("audience_description", _AUDIENCE_PLACEHOLDER)

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
        "Audience description (be specific — what behavior, what role, what's currently in the way?)",
        value=saved_audience,
        height=180,
        placeholder=_AUDIENCE_PLACEHOLDER,
        help=_AUDIENCE_HELP,
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

    st.subheader("Step 3 — Generate + Edit Design Doc")

    cached_doc = state.get("design_doc")

    if cached_doc is None:
        if st.button("🪄 Generate", type="primary"):
            inputs = _wizard_inputs_from_state()
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


def _step_build():
    import os
    from pathlib import Path

    from growme.assessment.generator import generate_program_assessment
    from growme.decks.builder import build_deck, collect_image_prompts
    from growme.decks.images import generate_deck_images
    from growme.decks.llm import (
        gen_facilitator_guide,
        gen_manager_briefing,
        plan_deck_audited,
    )
    from growme.pedagogy.auditor import render_audit_summary_md
    from growme.decks.pptx import export_pptx
    from growme.decks.render import render_deck
    from growme.sessions.plan_node import run as run_plan

    st.subheader("Step 4 — Build")

    deck = state.get("deck")

    if deck is None:
        enriched = state.get("enriched_context")
        edited_md = state.get("design_doc_edited_md")
        if enriched is None or edited_md is None:
            st.error("Step 3 hasn't run. Go back and click 🪄 Generate.")
            if st.button("← Back to Step 3"):
                _go_to(2)
                st.rerun()
            return

        if st.button("🚀 Build", type="primary"):
            inputs = _wizard_inputs_from_state()
            session_uuid = state.session_uuid()
            session_dir = Path(os.environ.get("GROWME_SESSION_DIR", ".growme_sessions")) / session_uuid
            session_dir.mkdir(parents=True, exist_ok=True)

            with st.status("Generating session plan + assessment + deck...", expanded=True) as s:
                try:
                    s.write("Session plan...")
                    plan = run_plan(edited_md, enriched, inputs)
                    state.update("session_plan", plan)
                    s.write("Assessment (3 frequency questions + commitments)...")
                    try:
                        assessment = generate_program_assessment(enriched, inputs)
                    except Exception as e:
                        st.warning(f"Live assessment generation failed ({e}); using offline template.")
                        from growme.assessment.generator import generate_program_assessment_offline
                        assessment = generate_program_assessment_offline(inputs.selected_behavior_ids)
                    state.update("program_assessment", assessment)
                    s.write("Planning deck (gpt-5.1, ~30s) + anti-slop audit pass...")
                    deck_plan, audit_report = plan_deck_audited(plan, enriched)
                    if audit_report is not None and audit_report.overall_grade != "pass":
                        state.update("deck_audit_report", audit_report)
                    else:
                        state.update("deck_audit_report", None)
                    s.write(f"Generating {len(collect_image_prompts(deck_plan))} hero images...")
                    image_paths = generate_deck_images(collect_image_prompts(deck_plan))
                    s.write("Facilitator guide...")
                    guide_md = gen_facilitator_guide(plan, enriched, deck_plan=deck_plan)
                    s.write("Manager 1:1 briefing (6-week prompt sheet)...")
                    try:
                        manager_briefing_md = gen_manager_briefing(
                            plan=plan,
                            enriched=enriched,
                            deck_plan=deck_plan,
                            design_doc_md=edited_md,
                        )
                    except Exception as e:
                        st.warning(f"Manager briefing generation failed ({e}); shipping without it.")
                        manager_briefing_md = ""
                    s.write("Composing deck + exporting .pptx...")
                    base_url = os.environ.get("STREAMLIT_LOCAL_URL", "http://localhost:8501")
                    pre_qr_url = f"{base_url}/?assessment={session_uuid}&kind=pre"
                    post_qr_url = f"{base_url}/?assessment={session_uuid}&kind=post"
                    d = build_deck(
                        plan=plan, enriched=enriched, deck_plan=deck_plan,
                        pre_qr_url=pre_qr_url, post_qr_url=post_qr_url,
                        facilitator_guide_md=guide_md,
                        manager_briefing_md=manager_briefing_md,
                        image_paths=image_paths,
                        company_alias=inputs.company_alias,
                    )
                    pptx_path = session_dir / "deck.pptx"
                    export_pptx(d, pptx_path)
                    state.update("deck", d)
                    s.update(label="Done.", state="complete")
                except Exception as e:
                    s.update(label=f"Build failed: {e}", state="error")
                    st.error(
                        "Build failed mid-pipeline. Click 🚀 Build again to retry, "
                        "or ← Back to Step 3 if the design doc needs changes."
                    )
                    return
            st.rerun()
        return

    st.success("✅ Built!")

    audit_report = state.get("deck_audit_report")
    if audit_report is not None:
        st.warning(render_audit_summary_md(audit_report))

    col_actions, col_qr = st.columns([2, 1])
    with col_actions:
        if deck.pptx_path:
            st.download_button(
                "⬇ Download .pptx",
                data=Path(deck.pptx_path).read_bytes(),
                file_name="growme_deck.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                type="primary",
            )
        st.download_button(
            "⬇ Download facilitator guide (.md)",
            data=deck.facilitator_guide_md,
            file_name="facilitator_guide.md",
            mime="text/markdown",
        )
        if deck.manager_briefing_md:
            st.download_button(
                "⬇ Download manager 1:1 prompts (.md)",
                data=deck.manager_briefing_md,
                file_name="manager_1to1_prompts.md",
                mime="text/markdown",
                help="6-week 1:1 prompt sheet for the rep's manager. "
                     "Manager involvement is the single largest predictor of "
                     "training transfer.",
            )
        st.caption("▶ Switch to **Demo Console** in the sidebar to run the simulation.")
    with col_qr:
        from growme.qr import generate_qr_png
        st.image(generate_qr_png(deck.pre_qr_url), caption="Pre-poll QR")
        st.image(generate_qr_png(deck.post_qr_url), caption="Post-poll QR")

    st.divider()
    st.subheader("Deck preview")
    render_deck(deck)


def _wizard_inputs_from_state():
    from growme.schemas import WizardInputs
    return WizardInputs(
        company_url=state.get("company_url"),
        company_alias=state.get("company_alias"),
        audience_description=state.get("audience_description"),
        selected_behavior_ids=state.get("selected_behavior_ids"),
    )
