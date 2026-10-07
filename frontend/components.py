"""Module 4: Streamlit UI Components and Layouts.

Encapsulates all presentation logic, state management, and tab views for the application.
Adheres strictly to separation of concerns by interacting exclusively with backend.services.
"""

import inspect
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import streamlit as st

import frontend.charts as charts
from backend.services import (
    build_report_csv,
    build_report_markdown,
    get_dataset_insights,
    get_example_students,
    get_full_report,
    get_input_spec,
    get_model_insights,
    get_roles,
    get_ui_config,
    run_what_if,
)

UI_CFG = get_ui_config()
STATUS_COLORS = UI_CFG["status_colors"]
RISK_COLORS = UI_CFG["risk_colors"]
SEVERITY_COLORS = UI_CFG["severity_colors"]
BRAND_COLOR = UI_CFG["brand_color"]
ACCENT_COLOR = UI_CFG["accent_color"]


def stretch_kwargs(func: Any) -> Dict[str, Any]:
    """Inspect function signature and return stretch-compatible width arguments."""
    try:
        sig = inspect.signature(func)
        if "width" in sig.parameters:
            return {"width": "stretch"}
        if "use_container_width" in sig.parameters:
            return {"use_container_width": True}
    except Exception:
        pass
    return {}


def inject_css() -> None:
    """Inject CSS tokens for card layouts, badges, and responsive containers."""
    css = """
    <style>
    div[data-testid="stMetric"] {
        background-color: rgba(154, 165, 177, 0.08);
        border: 1px solid rgba(154, 165, 177, 0.2);
        border-radius: 8px;
        padding: 12px 16px;
    }
    .badge-tag {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
        color: #FFFFFF !important;
    }
    .rec-box {
        background-color: rgba(154, 165, 177, 0.06);
        border-left: 4px solid #4F6DF5;
        padding: 12px 16px;
        margin-bottom: 12px;
        border-radius: 0px 8px 8px 0px;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def badge(text: str, color: str) -> str:
    """Format HTML span badge with accessible textual status and color styling."""
    return f'<span class="badge-tag" style="background-color: {color};">{text}</span>'


def show_status_error(status: Dict[str, Any]) -> None:
    """Render helpful error message detailing missing assets and repair commands."""
    st.error("Application setup incomplete. Some required model or data assets are missing.")
    if status.get("missing"):
        st.write("**Missing Files:**")
        for m in status["missing"]:
            st.markdown(f"- `{m}`")
    if status.get("fix_commands"):
        st.write("**Run the following pipeline commands from the project root:**")
        st.code("\n".join(status["fix_commands"]), language="bash")


@st.cache_data(show_spinner=False)
def cached_report(
    student_items: Tuple[Tuple[str, Any], ...],
    role: Optional[str] = None,
) -> Dict[str, Any]:
    """Cached wrapper around get_full_report accepting hashable student tuples."""
    student = dict(student_items)
    return get_full_report(student, role)


@st.cache_data(show_spinner=False)
def cached_what_if(
    student_items: Tuple[Tuple[str, Any], ...],
    changes_items: Tuple[Tuple[str, Any], ...],
    role: Optional[str] = None,
) -> Dict[str, Any]:
    """Cached wrapper around run_what_if accepting hashable tuple arguments."""
    student = dict(student_items)
    changes = dict(changes_items)
    return run_what_if(student, changes, role)


@st.cache_data(show_spinner=False)
def cached_dataset_insights() -> Dict[str, Any]:
    """Cached wrapper around get_dataset_insights."""
    return get_dataset_insights()


@st.cache_data(show_spinner=False)
def cached_model_insights() -> Dict[str, Any]:
    """Cached wrapper around get_model_insights."""
    return get_model_insights()


def _on_example_change() -> None:
    """Session state callback to populate input fields when selecting an example profile."""
    choice = st.session_state.get("example_choice")
    examples = get_example_students()
    if choice in examples:
        for k, v in examples[choice].items():
            st.session_state[f"inp_{k}"] = v


def render_header() -> None:
    """Render application banner, title, subtitle, and description."""
    st.title(f"{UI_CFG['app_icon']} {UI_CFG['app_title']}")
    st.caption(UI_CFG["app_subtitle"])


def render_sidebar() -> Tuple[Dict[str, float], str]:
    """Render interactive profile configuration sidebar and return active inputs."""
    st.sidebar.header("Profile Configuration")

    examples = get_example_students()
    example_names = list(examples.keys()) + [UI_CFG["custom_profile_label"]]

    if "example_choice" not in st.session_state:
        st.session_state["example_choice"] = example_names[0]

    st.sidebar.selectbox(
        "Load Example Profile",
        options=example_names,
        key="example_choice",
        on_change=_on_example_change,
        help="Select a benchmark profile or customize metrics below.",
    )

    spec = get_input_spec()

    # Initialize input session state keys if not set
    for item in spec:
        key = f"inp_{item['key']}"
        if key not in st.session_state:
            st.session_state[key] = item["default"]

    # Render inputs partitioned by group
    current_group = None
    for item in spec:
        grp = item["group"]
        if grp != current_group:
            st.sidebar.subheader(grp)
            current_group = grp

        k = item["key"]
        key = f"inp_{k}"
        lbl = item["label"]
        hlp = item["help"]

        if grp == "Technical Skills" or grp == "Soft Skills":
            st.sidebar.slider(
                lbl,
                min_value=item["min"],
                max_value=item["max"],
                step=item["step"],
                key=key,
                help=hlp,
            )
        elif item["type"] == "float":
            st.sidebar.number_input(
                lbl,
                min_value=item["min"],
                max_value=item["max"],
                step=item["step"],
                format="%.1f",
                key=key,
                help=hlp,
            )
        else:
            st.sidebar.number_input(
                lbl,
                min_value=item["min"],
                max_value=item["max"],
                step=item["step"],
                key=key,
                help=hlp,
            )

    # Build student dictionary with proper types
    student_dict: Dict[str, float] = {}
    for item in spec:
        k = item["key"]
        val = st.session_state[f"inp_{k}"]
        student_dict[k] = int(val) if item["type"] == "int" else float(val)

    st.sidebar.markdown("---")
    st.sidebar.subheader("Target Career Track")
    roles = get_roles()
    role_names = [r["name"] for r in roles]

    if "role_choice" not in st.session_state:
        st.session_state["role_choice"] = role_names[0]

    selected_role = st.sidebar.selectbox(
        "Select Target Role",
        options=role_names,
        key="role_choice",
    )
    role_desc = next((r["description"] for r in roles if r["name"] == selected_role), "")
    if role_desc:
        st.sidebar.caption(role_desc)

    return student_dict, selected_role


def render_downloads(report: Dict[str, Any]) -> None:
    """Render export download buttons for Markdown and CSV dossiers in sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.subheader("Export Dossier")
    md_content = build_report_markdown(report)
    csv_content = build_report_csv(report)

    st.sidebar.download_button(
        "Download Report (Markdown)",
        data=md_content,
        file_name="placement_readiness_report.md",
        mime="text/markdown",
        key="dl_markdown",
        **stretch_kwargs(st.sidebar.download_button),
    )
    st.sidebar.download_button(
        "Download Summary (CSV)",
        data=csv_content,
        file_name="placement_summary.csv",
        mime="text/csv",
        key="dl_csv",
        **stretch_kwargs(st.sidebar.download_button),
    )


def render_prediction_tab(report: Dict[str, Any]) -> None:
    """Render placement probability, readiness score, expected salary, and risk overview."""
    st.info(report["headline"])

    # Best-fit callout
    role_comp = report.get("role_comparison", [])
    if role_comp:
        best_role = role_comp[0]
        cur_role = report["role"]
        if best_role["role"] != cur_role:
            st.caption(
                f"Note: Based on your current strengths, you have highest alignment with "
                f"**{best_role['role']}** ({best_role['role_fit_pct']}%), compared to "
                f"{cur_role} ({next(r['role_fit_pct'] for r in role_comp if r['role'] == cur_role)}%)."
            )

    pred = report["prediction"]

    # Visual gauge row
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig_prob = charts.probability_gauge(pred["probability_pct"], pred["risk_level"])
        st.plotly_chart(fig_prob, key="pred_prob_gauge", **stretch_kwargs(st.plotly_chart))
    with col_g2:
        fig_read = charts.readiness_gauge(pred["readiness_score"])
        st.plotly_chart(fig_read, key="pred_read_gauge", **stretch_kwargs(st.plotly_chart))

    # Metric card row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Placement Probability", f"{pred['probability_pct']}%")
    with m2:
        st.metric("Readiness Score", f"{pred['readiness_score']} / 100")
    with m3:
        sal_range = pred["salary_range"]["label"]
        st.metric("Expected Package", sal_range)
        st.caption("if placed")
    with m4:
        r_color = RISK_COLORS.get(pred["risk_level"], BRAND_COLOR)
        st.metric("Risk Level", pred["risk_level"])
        st.markdown(badge(pred["risk_level"], r_color), unsafe_allow_html=True)

    # Engineered score progress bars
    st.subheader("Sub-Domain Composite Scores")
    eng = pred.get("engineered_scores", {})
    e1, e2 = st.columns(2)
    with e1:
        st.write(f"**Technical Skill Score:** {eng.get('tech_score', 0.0)} / 10")
        st.progress(min(max(float(eng.get("tech_score", 0.0)) / 10.0, 0.0), 1.0))
        st.write(f"**Soft Skills & Aptitude:** {eng.get('soft_score', 0.0)} / 10")
        st.progress(min(max(float(eng.get("soft_score", 0.0)) / 10.0, 0.0), 1.0))
    with e2:
        st.write(f"**Practical Experience Score:** {eng.get('experience_score', 0.0)} / 10")
        st.progress(min(max(float(eng.get("experience_score", 0.0)) / 10.0, 0.0), 1.0))
        st.write(f"**Academic Track Score:** {eng.get('academic_score', 0.0)} / 10")
        st.progress(min(max(float(eng.get("academic_score", 0.0)) / 10.0, 0.0), 1.0))

    # Cohort peer comparison
    peer = report.get("peer")
    if peer is not None:
        st.subheader("Cohort Standing")
        fig_peer = charts.peer_percentile_bar(peer)
        st.plotly_chart(fig_peer, key="pred_peer_bar", **stretch_kwargs(st.plotly_chart))

    st.caption(f"**Disclaimer:** {report['disclaimer']}")


def render_skill_gap_tab(report: Dict[str, Any]) -> None:
    """Render role-relative skill radar, gap bars, color-coded status tables, and profile checks."""
    skills_data = report["skills"]
    counts = skills_data["counts"]

    # Metrics row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Role Fit", f"{skills_data['role_fit_pct']}%")
    with c2:
        st.metric("Proficient (Good)", counts.get("GOOD", 0))
    with c3:
        st.metric("Moderate Gaps", counts.get("MODERATE", 0))
    with c4:
        st.metric("Critical Gaps (Weak)", counts.get("WEAK", 0))

    # Radar & Bar visualization side by side
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        fig_radar = charts.radar_chart(report["radar"])
        st.plotly_chart(fig_radar, key="sg_radar", **stretch_kwargs(st.plotly_chart))
    with col_v2:
        fig_gap = charts.skill_gap_bar(skills_data["skill_status"])
        st.plotly_chart(fig_gap, key="sg_bar", **stretch_kwargs(st.plotly_chart))

    # Styled skill breakdown table
    st.subheader("Detailed Skill Assessment")
    table_rows = []
    for s, st_info in skills_data["skill_status"].items():
        table_rows.append({
            "Skill": st_info["label"],
            "Your Score": st_info["score"],
            "Target": st_info["benchmark"],
            "Gap": st_info["gap"],
            "Status": st_info["status"],
            "Priority Score": st_info["priority_score"],
        })
    df_skills = pd.DataFrame(table_rows)

    def _highlight_status(val: str) -> str:
        color = STATUS_COLORS.get(val, "")
        if color:
            return f"color: {color}; font-weight: bold;"
        return ""

    try:
        styler = df_skills.style
        map_fn = getattr(styler, "map", getattr(styler, "applymap", None))
        if map_fn:
            styled_df = map_fn(_highlight_status, subset=["Status"])
            st.dataframe(styled_df, **stretch_kwargs(st.dataframe))
        else:
            st.dataframe(df_skills, **stretch_kwargs(st.dataframe))
    except Exception:
        st.dataframe(df_skills, **stretch_kwargs(st.dataframe))

    # Priority list
    priority_list = skills_data.get("priority_list", [])
    if priority_list:
        st.subheader("Priority Action Queue")
        for item in priority_list:
            c = STATUS_COLORS.get(item["status"], BRAND_COLOR)
            st.markdown(
                f"**{item['rank']}. {item['label']}** - Gap: {int(item['gap'])} "
                f"({badge(item['status'], c)}) - Priority Weight: {item['priority_score']:.1f}",
                unsafe_allow_html=True,
            )

    # Profile criteria checks
    st.subheader("Profile Requirements Check")
    prof_status = skills_data.get("profile_status", {})
    prof_rows = []
    for k, p in prof_status.items():
        prof_rows.append({
            "Requirement Area": p["label"],
            "Current Standing": p["current"],
            "Required Threshold": p["target"],
            "Compliance Status": "MET" if p["met"] else "NOT MET",
        })
    df_prof = pd.DataFrame(prof_rows)
    st.dataframe(df_prof, **stretch_kwargs(st.dataframe))

    # Role comparison bar
    st.subheader("Alternative Role Alignment")
    fig_role = charts.role_comparison_bar(report["role_comparison"])
    st.plotly_chart(fig_role, key="sg_role_comp", **stretch_kwargs(st.plotly_chart))


def render_recommendations_tab(report: Dict[str, Any]) -> None:
    """Render prioritized strategic interventions, impact rankings, and roadmap items."""
    bench_sim = report["benchmark_simulation"]
    b_prob = bench_sim["before"]["probability_pct"]
    a_prob = bench_sim["after"]["probability_pct"]
    st.markdown(
        f'<div class="rec-box"><h4 style="margin:0;">Target Goal Roadmap</h4>'
        f'Reaching every skill benchmark boosts your placement probability from '
        f'<strong>{b_prob}%</strong> to <strong>{a_prob}%</strong>.</div>',
        unsafe_allow_html=True,
    )

    recs = report.get("recommendations", [])
    if not recs or (len(recs) == 1 and recs[0]["area"] == "overall"):
        st.success(recs[0]["action"] if recs else "Your profile currently meets all benchmarks.")
        return

    # Severity filtering
    sev_filter = st.multiselect(
        "Filter Interventions by Urgency",
        options=["HIGH", "MEDIUM", "LOW"],
        default=["HIGH", "MEDIUM", "LOW"],
    )

    filtered_recs = [r for r in recs if r.get("severity") in sev_filter]

    st.subheader("Prioritized Interventions")
    for r in filtered_recs:
        sev = r["severity"]
        sev_col = SEVERITY_COLORS.get(sev, BRAND_COLOR)
        gain_str = (
            f" <span style='color:#2E9E5B; font-weight:600;'>(+{r['expected_gain_pct']}%)</span>"
            if r.get("expected_gain_pct") is not None and r["expected_gain_pct"] > 0
            else ""
        )
        curr_tgt = (
            f" [Current: {r['current']} -> Target: {r['target']}]"
            if r.get("current") is not None and r.get("target") is not None
            else ""
        )
        st.markdown(
            f"**#{r['rank']} {r['label']}** {badge(sev, sev_col)}{gain_str}{curr_tgt}",
            unsafe_allow_html=True,
        )
        st.write(r["action"])
        st.markdown("---")

    # Impact chart
    impact = report.get("impact", [])
    if impact:
        st.subheader("Expected Probability Yield (Single Intervention)")
        fig_impact = charts.impact_bar(impact)
        st.plotly_chart(fig_impact, key="rec_impact_bar", **stretch_kwargs(st.plotly_chart))


def render_whatif_tab(report: Dict[str, Any]) -> None:
    """Render interactive scenario simulation engine and quantify metric sensitivity."""
    st.caption("Adjust sliders to test prospective skill improvements. Values represent new absolute ratings.")

    student = report["student"]
    role = report["role"]
    spec = get_input_spec()
    spec_map = {item["key"]: item for item in spec}

    # State signature management: reset sliders if student or role changes
    sig = tuple(sorted(student.items())) + (role,)
    if st.session_state.get("wi_signature") != sig:
        st.session_state["wi_signature"] = sig
        for feat in UI_CFG["whatif_features"]:
            st.session_state[f"wi_{feat}"] = student[feat]

    def _reset_what_if() -> None:
        for feat in UI_CFG["whatif_features"]:
            st.session_state[f"wi_{feat}"] = student[feat]

    def _raise_skills_to_benchmark() -> None:
        for skill in UI_CFG["whatif_features"]:
            st_info = report["skills"]["skill_status"].get(skill)
            if st_info:
                bench = st_info["benchmark"]
                cur = student[skill]
                st.session_state[f"wi_{skill}"] = max(cur, int(bench) if isinstance(cur, int) else float(bench))

    b_col1, b_col2 = st.columns([1, 2])
    with b_col1:
        st.button("Reset", key="btn_reset_whatif", on_click=_reset_what_if, **stretch_kwargs(st.button))
    with b_col2:
        st.button(
            "Raise all skills to role benchmark",
            key="btn_raise_benchmarks",
            on_click=_raise_skills_to_benchmark,
            **stretch_kwargs(st.button),
        )

    # Render whatif sliders
    slider_cols = st.columns(2)
    for idx, feat in enumerate(UI_CFG["whatif_features"]):
        col_target = slider_cols[idx % 2]
        item = spec_map[feat]
        key = f"wi_{feat}"
        with col_target:
            st.slider(
                item["label"],
                min_value=item["min"],
                max_value=item["max"],
                step=item["step"],
                key=key,
            )

    # Detect modifications
    changes: Dict[str, float] = {}
    for feat in UI_CFG["whatif_features"]:
        val = st.session_state[f"wi_{feat}"]
        if val != student[feat]:
            changes[feat] = val

    if not changes:
        st.info("Move any slider above to simulate the impact on your placement prospects.")
        return

    # Execute simulation via cached wrapper
    student_tuple = tuple(sorted(student.items()))
    changes_tuple = tuple(sorted(changes.items()))
    res = cached_what_if(student_tuple, changes_tuple, role)

    sim = res["simulation"]
    st.success(sim["summary"])

    # Before / After Comparison Metrics
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        b_p = sim["before"]["probability_pct"]
        a_p = sim["after"]["probability_pct"]
        d_p = sim["delta"]["probability_pct"]
        st.metric("Placement Probability", f"{a_p}%", f"{d_p:+.1f}%")
    with m2:
        b_r = sim["before"]["readiness_score"]
        a_r = sim["after"]["readiness_score"]
        d_r = sim["delta"]["readiness_score"]
        st.metric("Readiness Score", f"{a_r}", f"{d_r:+.1f}")
    with m3:
        b_s = sim["before"]["salary_estimate"]
        a_s = sim["after"]["salary_estimate"]
        d_s = sim["delta"]["salary_estimate"]
        st.metric("Expected Salary (LPA)", f"{a_s}", f"{d_s:+.1f}")
    with m4:
        r_risk = sim["after"]["risk_level"]
        r_col = RISK_COLORS.get(r_risk, BRAND_COLOR)
        risk_note = " (Shifted!)" if res["risk_changed"] else ""
        st.markdown(
            f'<div style="text-align:center; padding-top:8px;">'
            f'<div style="font-size:12px; opacity:0.8;">NEW RISK LEVEL</div>'
            f'{badge(r_risk + risk_note, r_col)}</div>',
            unsafe_allow_html=True,
        )

    # Visualization and change log
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        fig_sim = charts.before_after_bar(sim)
        st.plotly_chart(fig_sim, key="whatif_bar", **stretch_kwargs(st.plotly_chart))
    with col_w2:
        st.subheader("Applied Modifications")
        chg_rows = []
        for f_name, chg_data in sim["applied_changes"].items():
            chg_rows.append({
                "Feature": spec_map[f_name]["label"],
                "Original": chg_data["from"],
                "Modified": chg_data["to"],
            })
        st.dataframe(pd.DataFrame(chg_rows), **stretch_kwargs(st.dataframe))


def render_insights_tab() -> None:
    """Render institutional dataset diagnostics, model benchmarks, and EDA charts."""
    st.subheader("Institutional Placement Trends & Model Benchmarks")

    ds_insights = cached_dataset_insights()
    model_insights = cached_model_insights()

    # Overview Metrics
    o1, o2, o3, o4 = st.columns(4)
    with o1:
        st.metric("Total Cohort Size", f"{ds_insights['n_students']:,}")
    with o2:
        st.metric("Placement Rate", f"{ds_insights['placement_rate_pct']}%")
    with o3:
        st.metric("Median Package", f"{ds_insights['salary_stats']['median']} LPA")
    with o4:
        st.metric("90th Percentile Package", f"{ds_insights['salary_stats']['p90']} LPA")

    # Cohort Distribution Charts
    c_d1, c_d2 = st.columns(2)
    with c_d1:
        fig_donut = charts.placement_donut(
            ds_insights["placed_count"], ds_insights["not_placed_count"]
        )
        st.plotly_chart(fig_donut, key="ins_donut", **stretch_kwargs(st.plotly_chart))
    with c_d2:
        fig_sal = charts.salary_histogram(
            ds_insights["salary_hist"], ds_insights["salary_stats"]
        )
        st.plotly_chart(fig_sal, key="ins_sal_hist", **stretch_kwargs(st.plotly_chart))

    # Skill and Experience Drivers
    s_c1, s_c2 = st.columns(2)
    with s_c1:
        fig_skills = charts.skill_means_bar(ds_insights["skill_means"])
        st.plotly_chart(fig_skills, key="ins_skill_means", **stretch_kwargs(st.plotly_chart))
    with s_c2:
        intern_data = ds_insights["placement_rate_by_internships"]
        fig_intern = charts.rate_bar(
            intern_data["labels"],
            intern_data["rates"],
            "Placement Rate by Internships",
            "Internships Completed",
        )
        st.plotly_chart(fig_intern, key="ins_intern_rates", **stretch_kwargs(st.plotly_chart))

    # Academic CGPA Bands
    cgpa_data = ds_insights["placement_rate_by_cgpa_band"]
    fig_cgpa = charts.rate_bar(
        cgpa_data["labels"],
        cgpa_data["rates"],
        "Placement Probability by CGPA Bracket",
        "CGPA Bracket",
    )
    st.plotly_chart(fig_cgpa, key="ins_cgpa_rates", **stretch_kwargs(st.plotly_chart))

    # Model Performance Evaluation
    st.markdown("---")
    st.subheader("Machine Learning Performance & Validation")

    clf_meta = model_insights["classifier"]
    st.markdown(f"**Selected Placement Classifier:** `{clf_meta['best_model']}`")
    st.caption(clf_meta["selection_reason"])
    df_clf = pd.DataFrame(clf_meta["rows"])
    st.dataframe(df_clf, **stretch_kwargs(st.dataframe))
    st.caption(f"Baseline Test Brier Score (Dummy Model): {clf_meta['baseline_brier']:.4f}")

    reg_meta = model_insights["regressor"]
    st.markdown(f"**Selected Salary Regressor:** `{reg_meta['best_model']}`")
    df_reg = pd.DataFrame(reg_meta["rows"])
    st.dataframe(df_reg, **stretch_kwargs(st.dataframe))
    st.caption(f"Baseline Test RMSE: {reg_meta['baseline_rmse']:.4f} LPA")

    # Feature Importances
    fi_col1, fi_col2 = st.columns(2)
    with fi_col1:
        fig_fi_clf = charts.feature_importance_bar(
            model_insights["feature_importance"]["classifier"],
            "Classifier Permutation Importance",
        )
        st.plotly_chart(fig_fi_clf, key="ins_fi_clf", **stretch_kwargs(st.plotly_chart))
    with fi_col2:
        fig_fi_reg = charts.feature_importance_bar(
            model_insights["feature_importance"]["regressor"],
            "Regressor Permutation Importance",
        )
        st.plotly_chart(fig_fi_reg, key="ins_fi_reg", **stretch_kwargs(st.plotly_chart))

    # Expandable gallery of figures
    figures = model_insights.get("figures", [])
    if figures:
        with st.expander("Saved Training and EDA Artifacts"):
            f_cols = st.columns(2)
            for idx, fig_meta in enumerate(figures):
                target_col = f_cols[idx % 2]
                with target_col:
                    st.image(
                        fig_meta["path"],
                        caption=fig_meta["title"],
                        **stretch_kwargs(st.image),
                    )

    st.caption(
        "**Methodological Limitations:** Dataset is synthetically derived based on latent "
        "effort factors and institutional recruitment heuristics. Salary estimates represent "
        "expected packages conditional on placement outcome. Correlation does not imply direct causation."
    )
