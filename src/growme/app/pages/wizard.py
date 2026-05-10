# src/growme/app/pages/wizard.py
"""4-step wizard with hackathon UI (theme, cards, training track)."""
from __future__ import annotations

from html import escape

import streamlit as st

from growme.app import audience_compose, state
from growme.app.ui.styles import inject_global_css

STEPS_INTERNAL = ["setup", "behaviors", "design", "build"]

# User-facing copy (3 phases in header; internal step 3–4 share phase 3)
STEP_LABELS_USER = [
    (1, "Program setup"),
    (2, "Training objectives"),
    (3, "Design approval"),
    (3, "Program materials"),
]

TRAINING_TRACKS: list[tuple[str, str]] = [
    ("sales_enablement", "Sales enablement"),
    ("leadership_development", "Leadership development"),
    ("it_systems", "IT systems"),
]

# UI-only placeholders (not wired to research).
_PLACEHOLDER_LEADERSHIP: list[tuple[str, str, str]] = [
    ("ld_demo_0", "Delegate decisions with clarity", "Managers assign outcomes, not tasks, with explicit checkpoints."),
    ("ld_demo_1", "Give feedback that changes behavior", "Timely, specific feedback tied to role standards and follow-up."),
    ("ld_demo_2", "Run inclusive 1:1s", "Balanced airtime, psychological safety, and documented commitments."),
    ("ld_demo_3", "Coach for accountability", "Shift from rescuing to questions that build ownership."),
    ("ld_demo_4", "Set boundaries on workload", "Prioritize, say no with context, and protect deep work."),
    ("ld_demo_5", "Model growth mindset", "Normalize learning from misses; celebrate experimentation."),
]

_PLACEHOLDER_IT: list[tuple[str, str, str]] = [
    ("it_demo_0", "Follow change-window process", "Use CAB templates and rollback criteria for every deploy."),
    ("it_demo_1", "Document runbooks before handoff", "Single source of truth with alarms, dashboards, and escalation."),
    ("it_demo_2", "Verify access with least privilege", "Role-based access reviews tied to ticket IDs."),
    ("it_demo_3", "Automate repetitive toil", "Replace manual steps with idempotent scripts or pipelines."),
    ("it_demo_4", "Treat incidents as learning", "Blameless postmortems with action items and owners."),
    ("it_demo_5", "Secure configuration baselines", "Drift detection and enforced standards in CI/CD."),
]

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

_AUDIENCE_PRESETS = [
    "Enterprise AEs",
    "Mid-market AEs",
    "SDRs / BDRs",
    "Customer success managers",
    "Sales engineers",
    "Frontline managers",
    "Other (describe in notes)",
]

_COHORT_SIZES = [
    "1–9 participants",
    "10–20 participants",
    "21–40 participants",
    "40+ participants",
]

_PROGRAM_FORMATS = [
    "Single session (demo)",
    "Half day",
    "Multi-week cohort",
]


def _current_step() -> int:
    return st.session_state.setdefault("wizard_step", 0)


def _go_to(step: int) -> None:
    st.session_state["wizard_step"] = max(0, min(len(STEPS_INTERNAL) - 1, step))


def _progress_pct(internal_step: int) -> int:
    if internal_step <= 0:
        return 33
    if internal_step == 1:
        return 66
    return 100


def _render_header(internal_step: int, page_title: str, subtitle: str) -> None:
    user_num, user_label = STEP_LABELS_USER[internal_step]
    pct = _progress_pct(internal_step)
    st.markdown(
        f'<div class="growme-progress-wrap">'
        f'<span>Step {user_num} of 3</span>'
        f'<div class="growme-progress-bar">'
        f'<div class="growme-progress-fill" style="width:{pct}%"></div>'
        f"</div>"
        f"<span>{user_label}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f'<p class="growme-page-title">{page_title}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="growme-subtitle">{subtitle}</p>', unsafe_allow_html=True)


def render() -> None:
    inject_global_css()

    step = _current_step()
    st.markdown('<div class="growme-page-title" style="margin-bottom:0.25rem">GrowMe</div>', unsafe_allow_html=True)
    st.caption("Behavior-change program wizard")

    cols = st.columns(len(STEPS_INTERNAL))
    labels = ["Setup", "Objectives", "Design", "Build"]
    for i, label in enumerate(labels):
        cols[i].markdown(f"**{i + 1}. {label}**" if i == step else f"{i + 1}. {label}")

    st.divider()

    if step == 0:
        _step_program_setup()
    elif step == 1:
        _step_behaviors()
    elif step == 2:
        _step_design_approval()
    elif step == 3:
        _step_build()


def _step_program_setup() -> None:
    _render_header(
        0,
        "Program setup",
        "Define the foundation of your program: organizational context, audience, and optional reference material.",
    )

    saved_url = state.get("company_url", "neon.tech")
    saved_alias = state.get("company_alias", "Photon DB")
    if "_prog_name_input" not in st.session_state:
        st.session_state["_prog_name_input"] = state.get("program_name", "")

    preset = state.get("audience_preset", _AUDIENCE_PRESETS[0])
    cohort = state.get("audience_cohort", _COHORT_SIZES[1])
    pfmt = state.get("audience_program_fmt", _PROGRAM_FORMATS[0])
    notes_val = state.get("audience_notes")
    if notes_val is None:
        legacy = state.get("audience_description") or ""
        if legacy.strip().startswith("Target audience:"):
            notes_val = ""
        else:
            notes_val = legacy.strip() or _AUDIENCE_PLACEHOLDER
    if not str(notes_val).strip():
        notes_val = _AUDIENCE_PLACEHOLDER

    left, right = st.columns([1.05, 0.95], gap="large")

    with left:
        st.markdown('<div class="growme-panel">', unsafe_allow_html=True)
        st.markdown("### Organizational context")
        st.text_input(
            "Program name (optional)",
            placeholder="e.g., Q2 leadership cohort",
            key="_prog_name_input",
        )
        pn = str(st.session_state.get("_prog_name_input") or "")
        company_url = st.text_input(
            "Company URL (used by research)",
            value=saved_url,
            help="The web crawler uses this URL.",
        )
        company_alias = st.text_input(
            "Organization display name",
            value=saved_alias,
            help="Shown in outputs; real name is aliased for the demo.",
        )
        st.caption("Reference documents (visual only — not sent to research yet)")
        up = st.file_uploader("Upload reference files", accept_multiple_files=True)
        if up is not None:
            state.update("uploaded_file_names", [f.name for f in up])
        names = state.get("uploaded_file_names") or []
        if names:
            pills = "".join(f'<span class="growme-pill">{escape(n)}</span>' for n in names)
            st.markdown(f'<div class="growme-pills">{pills}</div>', unsafe_allow_html=True)
        st.caption("Reference URLs (visual only)")
        url_a = st.text_input("Reference URL", value=(state.get("reference_urls") or ["", ""])[0], key="ref_url_0")
        url_b = st.text_input("Add another URL (optional)", value=(state.get("reference_urls") or ["", ""])[1], key="ref_url_1")
        state.update("reference_urls", [url_a.strip(), url_b.strip()])
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="growme-panel">', unsafe_allow_html=True)
        st.markdown("### Audience and format")
        i_preset = _AUDIENCE_PRESETS.index(preset) if preset in _AUDIENCE_PRESETS else 0
        i_cohort = _COHORT_SIZES.index(cohort) if cohort in _COHORT_SIZES else 1
        i_pfmt = _PROGRAM_FORMATS.index(pfmt) if pfmt in _PROGRAM_FORMATS else 0
        audience_preset = st.selectbox("Target audience", _AUDIENCE_PRESETS, index=i_preset)
        audience_cohort = st.selectbox("Cohort size", _COHORT_SIZES, index=i_cohort)
        audience_program_fmt = st.selectbox("Program format", _PROGRAM_FORMATS, index=i_pfmt)
        audience_notes = st.text_area(
            "Program brief and special instructions",
            value=notes_val,
            height=200,
            placeholder=_AUDIENCE_PLACEHOLDER,
            help=_AUDIENCE_HELP,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="growme-panel">', unsafe_allow_html=True)
    st.markdown("### Additional context")
    st.caption("Anything else the generator should know lives in the program brief above.")
    st.markdown("</div>", unsafe_allow_html=True)

    col_next = st.columns([1, 1, 1])
    with col_next[2]:
        if st.button("Continue to training objectives →", type="primary"):
            state.update("program_name", pn.strip())
            state.update("company_url", company_url.strip())
            state.update("company_alias", company_alias.strip())
            state.update("audience_preset", audience_preset)
            state.update("audience_cohort", audience_cohort)
            state.update("audience_program_fmt", audience_program_fmt)
            state.update("audience_notes", audience_notes.strip())
            state.update(
                "audience_description",
                audience_compose.compose_audience_description(
                    target_audience=audience_preset,
                    cohort_size=audience_cohort,
                    program_format=audience_program_fmt,
                    notes=audience_notes.strip(),
                ),
            )
            _go_to(1)
            st.rerun()


def _step_behaviors() -> None:
    from growme.behavior_menu import BEHAVIOR_MENU, default_pic_behavior_ids

    _render_header(
        1,
        "Training objectives",
        "Choose your training track, then pick exactly three target behaviors.",
    )

    track_labels = [t[1] for t in TRAINING_TRACKS]
    track_ids = [t[0] for t in TRAINING_TRACKS]
    current = state.get("training_track", "sales_enablement")
    idx = track_ids.index(current) if current in track_ids else 0
    choice = st.radio(
        "Training type",
        track_labels,
        index=idx,
        horizontal=True,
        key="growme_training_track_radio",
    )
    track = track_ids[track_labels.index(choice)]
    state.update("training_track", track)

    sales = track == "sales_enablement"

    if sales:
        st.markdown('<div class="growme-panel">', unsafe_allow_html=True)
        st.markdown("### Sales behaviors (pick exactly 3)")
        st.caption("Mapped to your existing research and design pipeline.")
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
        st.markdown("</div>", unsafe_allow_html=True)
        st.caption(f"Selected: {len(selected)} / 3")
        next_ok = len(selected) == 3
    else:
        st.info(
            "**Demo note:** Leadership and IT tracks show sample objectives only. "
            "Switch to **Sales enablement** to run research, design, and build end-to-end."
        )
        rows = _PLACEHOLDER_LEADERSHIP if track == "leadership_development" else _PLACEHOLDER_IT
        st.markdown('<div class="growme-panel">', unsafe_allow_html=True)
        st.markdown("### Sample behaviors (UI preview)")
        for bid, title, body in rows:
            st.markdown(f"**{title}**  \n_{body}_")
            st.checkbox("Select (preview only)", value=False, disabled=True, key=f"ph_{bid}")
        st.markdown("</div>", unsafe_allow_html=True)
        selected = []
        next_ok = False

    col_back, col_next = st.columns(2)
    if col_back.button("← Back"):
        _go_to(0)
        st.rerun()
    if col_next.button("Continue to design →", type="primary", disabled=not next_ok):
        if sales:
            state.update("selected_behavior_ids", selected)
        _go_to(2)
        st.rerun()


def _step_design_approval() -> None:
    from growme.design_doc.node import run as run_design_doc
    from growme.research.node import run as run_research

    _render_header(
        2,
        "Design approval",
        "Generate research-backed context, review the design document, then continue to build.",
    )

    cached_doc = state.get("design_doc")

    if cached_doc is None:
        st.markdown('<div class="growme-panel">', unsafe_allow_html=True)
        st.markdown("### Generate design document")
        st.caption("Runs Phase A/B research and writes the pedagogy-aligned design doc.")
        st.markdown("</div>", unsafe_allow_html=True)
        if st.button("Generate design document", type="primary"):
            inputs = _wizard_inputs_from_state()
            with st.status("Researching and drafting...", expanded=True) as s:
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
        if st.button("← Back to objectives"):
            _go_to(1)
            st.rerun()
        return

    st.markdown('<div class="growme-panel">', unsafe_allow_html=True)
    st.markdown("### Design document (editable)")
    st.caption("Approve by continuing to build, or edit inline before you ship.")
    edited = st.text_area(
        "Markdown",
        value=state.get("design_doc_edited_md", cached_doc.full_markdown),
        height=520,
        label_visibility="collapsed",
    )
    state.update("design_doc_edited_md", edited)
    st.markdown("</div>", unsafe_allow_html=True)

    col_back, col_mid, col_build = st.columns([1, 1, 1])
    if col_back.button("← Back to objectives"):
        _go_to(1)
        st.rerun()
    if col_mid.button("Regenerate (discard edits)", help="Clears cached doc and re-runs from scratch"):
        state.update("design_doc", None)
        state.update("design_doc_edited_md", None)
        state.update("enriched_context", None)
        st.rerun()
    if col_build.button("Continue to program materials →", type="primary"):
        _go_to(3)
        st.rerun()


def _step_build() -> None:
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
    from growme.qr import generate_qr_png
    from growme.sessions.plan_node import run as run_plan

    _render_header(
        3,
        "Program materials",
        "Build session assets, download outputs, and preview the deck.",
    )

    deck = state.get("deck")

    if deck is None:
        enriched = state.get("enriched_context")
        edited_md = state.get("design_doc_edited_md")
        if enriched is None or edited_md is None:
            st.markdown('<div class="growme-panel">', unsafe_allow_html=True)
            st.error("Generate the design document first.")
            st.markdown("</div>", unsafe_allow_html=True)
            if st.button("← Back to design"):
                _go_to(2)
                st.rerun()
            return

        st.markdown('<div class="growme-panel">', unsafe_allow_html=True)
        st.markdown("### Build session package")
        st.caption("Session plan, assessment, deck, facilitator guide, and optional manager prompts.")
        st.markdown("</div>", unsafe_allow_html=True)
        if st.button("Build program", type="primary"):
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
                    s.write("Planning deck + anti-slop audit pass...")
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
                        plan=plan,
                        enriched=enriched,
                        deck_plan=deck_plan,
                        pre_qr_url=pre_qr_url,
                        post_qr_url=post_qr_url,
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
                        "Build failed mid-pipeline. Click **Build program** again to retry, "
                        "or go back to design if the document needs changes."
                    )
                    return
            st.rerun()
        if st.button("← Back to design"):
            _go_to(2)
            st.rerun()
        return

    st.success("Build complete.")

    audit_report = state.get("deck_audit_report")
    if audit_report is not None:
        st.warning(render_audit_summary_md(audit_report))

    st.markdown('<div class="growme-panel">', unsafe_allow_html=True)
    st.markdown("### Program materials")
    st.caption("Download generated artifacts (same outputs as before, organized for review).")
    st.markdown("</div>", unsafe_allow_html=True)

    rows: list[tuple[str, str, bytes | str, str, str]] = []
    if deck.pptx_path:
        rows.append(
            (
                "Presentation",
                "growme_deck.pptx",
                Path(deck.pptx_path).read_bytes(),
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "Slide deck with polls and narrative",
            )
        )
    rows.append(
        (
            "Guide",
            "facilitator_guide.md",
            deck.facilitator_guide_md,
            "text/markdown",
            "Facilitator-facing session guide",
        )
    )
    if deck.manager_briefing_md:
        rows.append(
            (
                "Guide",
                "manager_1to1_prompts.md",
                deck.manager_briefing_md,
                "text/markdown",
                "Six-week 1:1 prompt sheet for managers",
            )
        )

    for kind, fname, data, mime, blurb in rows:
        c1, c2 = st.columns([2.2, 1])
        with c1:
            st.markdown(f"**{fname}**  \n_{kind}_ — {blurb}")
        with c2:
            st.download_button(
                "Download",
                data=data,
                file_name=fname,
                mime=mime,
                type="primary",
                key=f"dl_{fname}",
            )

    st.divider()
    st.markdown("### Poll QR codes")
    col_actions, col_qr = st.columns([2, 1])
    with col_actions:
        st.caption("Open the Demo Console in the sidebar to run the full simulation.")
    with col_qr:
        st.image(generate_qr_png(deck.pre_qr_url), caption="Pre-poll QR")
        st.image(generate_qr_png(deck.post_qr_url), caption="Post-poll QR")

    st.divider()
    st.subheader("Deck preview")
    render_deck(deck)


def _wizard_inputs_from_state():
    from growme.schemas import WizardInputs

    aud = state.get("audience_description")
    if not aud:
        aud = audience_compose.compose_audience_description(
            target_audience=state.get("audience_preset", _AUDIENCE_PRESETS[0]),
            cohort_size=state.get("audience_cohort", _COHORT_SIZES[1]),
            program_format=state.get("audience_program_fmt", _PROGRAM_FORMATS[0]),
            notes=state.get("audience_notes", ""),
        )
    return WizardInputs(
        company_url=state.get("company_url"),
        company_alias=state.get("company_alias"),
        audience_description=aud,
        selected_behavior_ids=state.get("selected_behavior_ids"),
    )
