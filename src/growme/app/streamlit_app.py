"""GrowMe Streamlit app entry. Multi-page wizard + Demo Console.

Run: streamlit run src/growme/app/streamlit_app.py
"""
from dotenv import load_dotenv

load_dotenv()

import streamlit as st  # noqa: E402

st.set_page_config(page_title="GrowMe", page_icon="🌱", layout="wide")

PAGES = {
    "Wizard": "wizard",
    "Demo Console": "demo_console",
}


def main():
    st.sidebar.title("GrowMe 🌱")
    page = st.sidebar.radio("Navigate", list(PAGES.keys()))
    if page == "Wizard":
        from growme.app.pages import wizard
        wizard.render()
    else:
        from growme.app.pages import demo_console
        demo_console.render()


if __name__ == "__main__":
    main()
