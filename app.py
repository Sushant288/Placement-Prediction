"""Application Entry Point. Thin entry point orchestrating layout, state, and dashboard rendering."""

import streamlit as st

from backend.services import get_app_status, get_ui_config
from frontend.components import (
    cached_report, inject_css, render_downloads, render_header,
    render_insights_tab, render_prediction_tab, render_recommendations_tab,
    render_sidebar, render_skill_gap_tab, render_whatif_tab, show_status_error,
)

cfg = get_ui_config()
st.set_page_config(page_title=cfg["app_title"], page_icon=cfg["app_icon"], layout="wide")

status = get_app_status()
if not status["ready"]:
    show_status_error(status)
    st.stop()

inject_css()
render_header()
student, role = render_sidebar()

try:
    student_tuple = tuple(sorted(student.items()))
    report = cached_report(student_tuple, role)
except ValueError as e:
    st.error(str(e))
    st.stop()
except FileNotFoundError as e:
    st.error(f"Required files not found: {e}")
    st.stop()
except Exception as e:
    st.error("Something went wrong while processing the profile.")
    with st.expander("Error Details"):
        st.exception(e)
    st.stop()

render_downloads(report)

tabs = st.tabs(cfg["tab_names"])
with tabs[0]:
    render_prediction_tab(report)
with tabs[1]:
    render_skill_gap_tab(report)
with tabs[2]:
    render_recommendations_tab(report)
with tabs[3]:
    render_whatif_tab(report)
with tabs[4]:
    render_insights_tab()
