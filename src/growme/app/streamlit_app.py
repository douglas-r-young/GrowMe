"""GrowMe Streamlit app entry. Multi-page wizard + Demo Console.

Run: streamlit run src/growme/app/streamlit_app.py
"""
from dotenv import load_dotenv

load_dotenv()

import os  # noqa: E402

import streamlit as st  # noqa: E402

from growme.app import state  # noqa: E402

st.set_page_config(page_title="GrowMe", page_icon="🌱", layout="wide")

PAGES = {
    "Wizard": "wizard",
    "Demo Console": "demo_console",
}


def main():
    qp = st.query_params
    target = qp.get("assessment")
    if isinstance(target, list):
        target = target[0] if target else None
    kind = qp.get("kind")
    if isinstance(kind, list):
        kind = kind[0] if kind else None
    if target:
        from growme.app.pages import assessment
        assessment.render(target_uuid=target, kind=kind or "pre")
        return

    st.sidebar.title("GrowMe 🌱")
    page = st.sidebar.radio("Navigate", list(PAGES.keys()))

    st.sidebar.divider()
    uid = state.session_uuid()
    st.sidebar.caption(f"Session: `{uid[:8]}`")

    base_url = os.environ.get("STREAMLIT_LOCAL_URL", "http://localhost:8501")
    if state.get("deck"):
        st.sidebar.markdown(f"[▶ Open pre-poll]({base_url}/?assessment={uid}&kind=pre)")
        st.sidebar.markdown(f"[▶ Open post-poll]({base_url}/?assessment={uid}&kind=post)")

    if st.sidebar.button("🔄 Reset session"):
        state.reset_session()
        st.rerun()

    if page == "Wizard":
        from growme.app.pages import wizard
        wizard.render()
    else:
        from growme.app.pages import demo_console
        demo_console.render()


if __name__ == "__main__":
    main()
