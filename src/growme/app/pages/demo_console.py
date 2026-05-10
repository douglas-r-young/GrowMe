"""Demo Console — single button that fast-forwards the whole simulation."""
from __future__ import annotations

import streamlit as st

from growme.app import state
from growme.assessment import fixtures as afix
from growme.assessment.fixtures import distribution
from growme.delta_report.node import run as run_delta
from growme.nudges.node import generate_for_post_responses


def render():
    st.title("Demo Console")
    st.caption("Fast-forward through simulated training time.")

    deck = state.get("deck")
    enriched = state.get("enriched_context")
    if not deck or not enriched:
        st.warning("Build the program first via the Wizard.")
        return

    sim = state.get("sim_complete", False)
    if not sim:
        if st.button("▶ Run full simulation", type="primary"):
            session_uuid = state.session_uuid()
            behavior_ids = deck.behavior_ids
            pre = afix.pre_responses(session_uuid, behavior_ids)
            post = afix.post_responses(session_uuid, behavior_ids)
            responses = pre + post
            state.update("assessment_responses", responses)
            with st.status("Running simulation...", expanded=True) as s:
                try:
                    s.write("Generating nudges...")
                    nudges = generate_for_post_responses(post, enriched)
                    state.update("nudges", nudges)
                    s.write("Generating delta report...")
                    report = run_delta(responses, enriched)
                    state.update("delta_report", report)
                    state.update("sim_complete", True)
                    s.update(label="Done.", state="complete")
                except Exception as e:
                    s.update(label=f"Simulation failed: {e}", state="error")
                    st.error(
                        "Simulation failed mid-pipeline. Click ▶ Run full simulation again to retry."
                    )
                    return
            st.rerun()
        return

    responses = state.get("assessment_responses", [])
    nudges = state.get("nudges", [])
    report = state.get("delta_report")

    st.success("Simulation complete.")

    st.subheader("Pre-program distribution")
    _render_distribution(responses, "pre", deck.behavior_ids)

    st.subheader("Post-program distribution")
    _render_distribution(responses, "post", deck.behavior_ids)

    st.subheader("Nudges (8 learners)")
    for n in nudges:
        with st.container(border=True):
            st.markdown(f"**{n.learner_id} — {n.email_subject}**")
            st.markdown(n.email_body_md)
            st.caption(f"Slack: {n.slack_text}")

    st.subheader("Delta report")
    if report:
        st.markdown(report.full_markdown)


def _render_distribution(responses, kind, behavior_ids):
    cols = st.columns(len(behavior_ids))
    for col, bid in zip(cols, behavior_ids):
        with col:
            dist = distribution(responses, kind, bid)
            st.caption(bid)
            for choice in ["Never", "Rarely", "Sometimes", "Often", "Always"]:
                if dist.get(choice):
                    st.write(f"- {choice}: {dist[choice]}")
