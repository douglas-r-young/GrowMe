"""Assessment page rendered when ?assessment=<uuid>&kind=<pre|post>.

Reads + writes the same pickle the wizard uses, scoped by session uuid.
"""
from __future__ import annotations

from typing import Literal

import streamlit as st

from growme.app import state as appstate
from growme.schemas import AssessmentResponse


def render(target_uuid: str, kind: Literal["pre", "post"]):
    st.title("Behavior Assessment")
    if kind not in ("pre", "post"):
        st.error("Missing or invalid `kind` query param. Use `?kind=pre` or `?kind=post`.")
        return

    # Hydrate from the wizard's session pickle (this URL bypasses the wizard's
    # in-memory st.session_state, so we explicitly point at target_uuid).
    appstate.set_session_uuid(target_uuid)
    assessment = appstate.get("program_assessment")
    if assessment is None:
        st.warning("Assessment not yet generated. Ask Linda to finish Step 4 of the wizard.")
        return

    prefix = "**Pre-program**" if kind == "pre" else "**Post-program**"
    st.markdown(f"{prefix} — answer honestly, this informs your training plan.")

    learner_name = st.text_input("Your name", value="")
    learner_id = st.text_input("Learner ID (or email)", value="")

    # `pre_questions` is the schema name; we re-use the same 3 questions for
    # the post form so deltas are computable. index=None forces a real choice
    # rather than silently defaulting to "Never".
    answers: dict[str, str | None] = {}
    for q in assessment.pre_questions:
        answers[q.behavior_id] = st.radio(
            q.prompt, q.options, index=None, key=f"q_{q.behavior_id}_{kind}"
        )

    commitment: str | None = None
    if kind == "post":
        commitment = st.selectbox(
            "Pick a commitment for the next 7 days",
            assessment.commitment_options,
            key="commit_choice",
        )

    if st.button("Submit", type="primary"):
        if not learner_name or not learner_id:
            st.error("Please fill in your name and learner ID first.")
            return
        if any(v is None for v in answers.values()):
            st.error("Please answer all 3 frequency questions before submitting.")
            return
        resp = AssessmentResponse(
            session_uuid=target_uuid,
            learner_id=learner_id,
            learner_name=learner_name,
            kind=kind,
            frequency_answers=answers,  # type: ignore[arg-type]
            commitment=commitment,
        )
        existing = appstate.get("assessment_responses", []) or []
        existing.append(resp)
        appstate.update("assessment_responses", existing)
        st.success("Thanks! Your response was recorded.")
        st.balloons()
