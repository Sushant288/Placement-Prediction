"""Module 4: Plotly Chart Builders.

Pure visualization functions returning Plotly Figure objects.
Maintains full theme adaptability (light/dark mode) without hardcoded background colors.
"""

from typing import Any, Dict, List, Optional

import plotly.graph_objects as go

from backend.services import get_ui_config

UI_CFG = get_ui_config()
BRAND_COLOR = UI_CFG["brand_color"]
ACCENT_COLOR = UI_CFG["accent_color"]
STATUS_COLORS = UI_CFG["status_colors"]
RISK_COLORS = UI_CFG["risk_colors"]
SEVERITY_COLORS = UI_CFG["severity_colors"]
RISK_LOW_PCT = UI_CFG["risk_low_pct"]
RISK_MED_PCT = UI_CFG["risk_medium_pct"]


def _empty_fig(title: str = "", message: str = "No data") -> go.Figure:
    """Return an empty figure with a centered explanatory annotation."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14, color=ACCENT_COLOR),
    )
    fig.update_layout(
        title=title,
        height=350,
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def probability_gauge(probability_pct: float, risk_level: str) -> go.Figure:
    """Build indicator gauge (0-100) with risk threshold zones and color-coded indicator."""
    if probability_pct is None:
        return _empty_fig("Placement Probability")

    bar_color = RISK_COLORS.get(risk_level, BRAND_COLOR)
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=float(probability_pct),
            number={"suffix": "%", "font": {"size": 36}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": bar_color, "thickness": 0.28},
                "steps": [
                    {"range": [0, RISK_MED_PCT], "color": "rgba(214, 69, 69, 0.22)"},
                    {"range": [RISK_MED_PCT, RISK_LOW_PCT], "color": "rgba(224, 161, 0, 0.22)"},
                    {"range": [RISK_LOW_PCT, 100], "color": "rgba(46, 158, 91, 0.22)"},
                ],
            },
        )
    )
    fig.update_layout(
        title={"text": "Placement Probability", "x": 0.5},
        height=320,
        margin=dict(l=30, r=30, t=60, b=20),
    )
    return fig


def readiness_gauge(score: float) -> go.Figure:
    """Build readiness score gauge (0-100) using brand theme styling."""
    if score is None:
        return _empty_fig("Readiness Score")

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=float(score),
            number={"suffix": " / 100", "font": {"size": 36}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": BRAND_COLOR, "thickness": 0.28},
                "steps": [
                    {"range": [0, 100], "color": "rgba(79, 109, 245, 0.12)"},
                ],
            },
        )
    )
    fig.update_layout(
        title={"text": "Overall Readiness Score", "x": 0.5},
        height=320,
        margin=dict(l=30, r=30, t=60, b=20),
    )
    return fig


def radar_chart(radar: Optional[Dict[str, Any]]) -> go.Figure:
    """Build closed polygon radar chart comparing candidate proficiencies against role benchmarks."""
    if not radar:
        return _empty_fig("Skill Profile Radar")
    labels = radar.get("labels", [])
    student_vals = radar.get("student", [])
    bench_vals = radar.get("benchmark", [])
    max_val = radar.get("max_value", 10)

    if not labels or not student_vals or not bench_vals:
        return _empty_fig("Skill Profile Radar")

    # Close polygons
    theta = list(labels) + [labels[0]]
    r_student = list(student_vals) + [student_vals[0]]
    r_bench = list(bench_vals) + [bench_vals[0]]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=r_bench,
            theta=theta,
            fill="toself",
            name="Role Benchmark",
            line=dict(color=ACCENT_COLOR, dash="dash"),
            fillcolor="rgba(154, 165, 177, 0.15)",
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=r_student,
            theta=theta,
            fill="toself",
            name="Candidate Score",
            line=dict(color=BRAND_COLOR, width=2.5),
            fillcolor="rgba(79, 109, 245, 0.25)",
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, max_val]),
        ),
        title={"text": "Candidate vs Benchmark Skill Radar", "x": 0.5},
        height=380,
        margin=dict(l=40, r=40, t=60, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
    )
    return fig


def skill_gap_bar(skill_status: Dict[str, Dict[str, Any]]) -> go.Figure:
    """Build horizontal bar chart of skills colored by status with benchmark markers."""
    if not skill_status:
        return _empty_fig("Skill Gap Breakdown")

    # Sort by gap desc
    items = sorted(skill_status.items(), key=lambda x: -x[1]["gap"])
    labels = [item[1]["label"] for item in items]
    scores = [item[1]["score"] for item in items]
    benchmarks = [item[1]["benchmark"] for item in items]
    colors = [STATUS_COLORS.get(item[1]["status"], BRAND_COLOR) for item in items]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=labels,
            x=scores,
            orientation="h",
            name="Score",
            marker=dict(color=colors),
            text=[f"{s:.0f}" for s in scores],
            textposition="auto",
        )
    )
    fig.add_trace(
        go.Scatter(
            y=labels,
            x=benchmarks,
            mode="markers",
            name="Benchmark",
            marker=dict(color="#1A202C", symbol="line-ns-open", size=18, line=dict(width=3)),
        )
    )

    fig.update_layout(
        title="Skill Scores vs Benchmarks (Sorted by Gap)",
        height=380,
        margin=dict(l=100, r=30, t=50, b=40),
        xaxis=dict(title="Score (1-10)", range=[0, 10.5]),
        yaxis=dict(autorange="reversed"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
    )
    return fig


def role_comparison_bar(role_comparison: List[Dict[str, Any]]) -> go.Figure:
    """Build horizontal bar chart of role alignment percentages highlighting selected role."""
    if not role_comparison:
        return _empty_fig("Role Alignment Comparison")

    roles = [item["role"] for item in role_comparison]
    fits = [item["role_fit_pct"] for item in role_comparison]
    colors = [BRAND_COLOR if item["is_selected"] else ACCENT_COLOR for item in role_comparison]

    fig = go.Figure(
        go.Bar(
            y=roles,
            x=fits,
            orientation="h",
            marker=dict(color=colors),
            text=[f"{f:.1f}%" for f in fits],
            textposition="outside",
        )
    )
    fig.update_layout(
        title="Role Alignment Fit (%)",
        height=320,
        margin=dict(l=120, r=40, t=50, b=40),
        xaxis=dict(title="Alignment Fit (%)", range=[0, 115]),
        yaxis=dict(autorange="reversed"),
    )
    return fig


def impact_bar(impact: List[Dict[str, Any]], top_n: int = 8) -> go.Figure:
    """Build horizontal bar chart of top single-intervention probability gains."""
    if not impact:
        return _empty_fig("Potential Intervention Impact", "All benchmarks currently met")

    top_items = impact[:top_n]
    labels = [item["label"] for item in top_items]
    gains = [item["gain_pct"] for item in top_items]
    colors = [BRAND_COLOR if g > 0 else ACCENT_COLOR for g in gains]

    fig = go.Figure(
        go.Bar(
            y=labels,
            x=gains,
            orientation="h",
            marker=dict(color=colors),
            text=[f"+{g:.1f}%" if g > 0 else f"{g:.1f}%" for g in gains],
            textposition="outside",
        )
    )
    max_x = max(max(gains) * 1.25, 2.0) if gains else 5.0
    fig.update_layout(
        title="Top Improvements by Placement Probability Gain",
        height=350,
        margin=dict(l=120, r=40, t=50, b=40),
        xaxis=dict(title="Probability Gain (%)", range=[0, max_x]),
        yaxis=dict(autorange="reversed"),
    )
    return fig


def before_after_bar(simulation: Optional[Dict[str, Any]]) -> go.Figure:
    """Build grouped bar chart comparing key metrics before and after simulated changes."""
    if not simulation:
        return _empty_fig("Simulation Outcome Comparison")
    before = simulation.get("before", {})
    after = simulation.get("after", {})

    if not before or not after:
        return _empty_fig("Simulation Outcome Comparison")

    categories = ["Placement Probability (%)", "Readiness Score (/100)"]
    val_before = [before.get("probability_pct", 0.0), before.get("readiness_score", 0.0)]
    val_after = [after.get("probability_pct", 0.0), after.get("readiness_score", 0.0)]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=categories,
            y=val_before,
            name="Before",
            marker=dict(color=ACCENT_COLOR),
            text=[f"{v:.1f}" for v in val_before],
            textposition="auto",
        )
    )
    fig.add_trace(
        go.Bar(
            x=categories,
            y=val_after,
            name="After (Simulated)",
            marker=dict(color=BRAND_COLOR),
            text=[f"{v:.1f}" for v in val_after],
            textposition="auto",
        )
    )

    fig.update_layout(
        barmode="group",
        title="Before vs After Simulation Comparison",
        height=340,
        margin=dict(l=40, r=40, t=50, b=40),
        yaxis=dict(title="Score / Percentage", range=[0, 110]),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
    )
    return fig


def peer_percentile_bar(peer: Optional[Dict[str, Dict[str, Any]]]) -> go.Figure:
    """Build horizontal bar chart depicting cohort percentile standings with median marker."""
    if not peer:
        return _empty_fig("Cohort Peer Comparison")

    labels = [v["label"] for v in peer.values()]
    pcts = [v["percentile"] for v in peer.values()]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=labels,
            x=pcts,
            orientation="h",
            marker=dict(color=BRAND_COLOR),
            text=[f"{p:.1f}%" for p in pcts],
            textposition="auto",
        )
    )
    fig.add_vline(x=50, line_width=2, line_dash="dash", line_color="#D64545", annotation_text="Cohort Median")

    fig.update_layout(
        title="Candidate Standing Relative to Historical Cohort",
        height=320,
        margin=dict(l=120, r=40, t=50, b=40),
        xaxis=dict(title="Percentile Rank (%)", range=[0, 100]),
        yaxis=dict(autorange="reversed"),
    )
    return fig


def feature_importance_bar(importance: Dict[str, float], title: str = "Feature Importance") -> go.Figure:
    """Build horizontal bar chart of top permutation feature importance scores."""
    if not importance:
        return _empty_fig(title)

    labels = list(importance.keys())[::-1]
    vals = list(importance.values())[::-1]

    fig = go.Figure(
        go.Bar(
            y=labels,
            x=vals,
            orientation="h",
            marker=dict(color=BRAND_COLOR),
        )
    )
    fig.update_layout(
        title=title,
        height=380,
        margin=dict(l=130, r=40, t=50, b=40),
        xaxis=dict(title="Permutation Importance Score"),
    )
    return fig


def model_comparison_bar(rows: List[Dict[str, Any]], metrics: List[str], title: str = "Model Comparison") -> go.Figure:
    """Build grouped bar chart comparing multiple machine learning models across key metrics."""
    if not rows or not metrics:
        return _empty_fig(title)

    models = [r["model"].replace("_", " ").title() for r in rows]
    fig = go.Figure()

    palette = [BRAND_COLOR, "#2E9E5B", "#E0A100", "#D64545", "#9AA5B1"]
    for idx, m in enumerate(metrics):
        vals = [r.get(m, 0.0) for r in rows]
        fig.add_trace(
            go.Bar(
                x=models,
                y=vals,
                name=m.replace("_", " ").upper(),
                marker=dict(color=palette[idx % len(palette)]),
                text=[f"{v:.3f}" for v in vals],
                textposition="auto",
            )
        )

    fig.update_layout(
        barmode="group",
        title=title,
        height=350,
        margin=dict(l=40, r=40, t=50, b=40),
        yaxis=dict(title="Metric Score"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
    )
    return fig


def placement_donut(placed_count: int, not_placed_count: int) -> go.Figure:
    """Build donut pie chart visualizing overall placement distribution in dataset."""
    if placed_count == 0 and not_placed_count == 0:
        return _empty_fig("Placement Ratio")

    labels = ["Placed", "Not Placed"]
    values = [placed_count, not_placed_count]
    colors = [STATUS_COLORS["GOOD"], STATUS_COLORS["WEAK"]]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.55,
            marker=dict(colors=colors),
            textinfo="label+percent",
        )
    )
    fig.update_layout(
        title={"text": "Historical Placement Split", "x": 0.5},
        height=320,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def salary_histogram(
    salary_hist: Optional[Dict[str, Any]],
    salary_stats: Optional[Dict[str, float]],
) -> go.Figure:
    """Build salary distribution histogram with median benchmark overlay."""
    if not salary_hist or not salary_stats:
        return _empty_fig("Salary Distribution")

    bin_edges = salary_hist.get("bin_edges", [])
    counts = salary_hist.get("counts", [])

    if not bin_edges or not counts:
        return _empty_fig("Salary Distribution")

    # Midpoints of bins for bar plotting
    mids = [(bin_edges[i] + bin_edges[i + 1]) / 2.0 for i in range(len(counts))]
    widths = [bin_edges[i + 1] - bin_edges[i] for i in range(len(counts))]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=mids,
            y=counts,
            width=widths,
            marker=dict(color="rgba(79, 109, 245, 0.7)", line=dict(color=BRAND_COLOR, width=1)),
            name="Students",
        )
    )

    median_val = salary_stats.get("median", 0.0)
    fig.add_vline(
        x=median_val,
        line_width=2,
        line_dash="dash",
        line_color="#D64545",
        annotation_text=f"Median: {median_val} LPA",
    )

    fig.update_layout(
        title="Package Distribution for Placed Students (LPA)",
        height=340,
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(title="Salary Package (LPA)"),
        yaxis=dict(title="Student Count"),
    )
    return fig


def skill_means_bar(skill_means: Optional[Dict[str, Any]]) -> go.Figure:
    """Build grouped bar chart comparing average skill assessments of placed vs unplaced cohorts."""
    if not skill_means:
        return _empty_fig("Average Skills: Placed vs Unplaced")

    labels = skill_means.get("labels", [])
    placed = skill_means.get("placed", [])
    unplaced = skill_means.get("not_placed", [])

    if not labels or not placed or not unplaced:
        return _empty_fig("Average Skills: Placed vs Unplaced")

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=labels,
            y=placed,
            name="Placed Students",
            marker=dict(color=STATUS_COLORS["GOOD"]),
            text=[f"{v:.1f}" for v in placed],
            textposition="auto",
        )
    )
    fig.add_trace(
        go.Bar(
            x=labels,
            y=unplaced,
            name="Unplaced Students",
            marker=dict(color=STATUS_COLORS["WEAK"]),
            text=[f"{v:.1f}" for v in unplaced],
            textposition="auto",
        )
    )

    fig.update_layout(
        barmode="group",
        title="Mean Skill Scores by Placement Outcome",
        height=350,
        margin=dict(l=40, r=40, t=50, b=40),
        yaxis=dict(title="Mean Score (1-10)", range=[0, 10]),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
    )
    return fig


def rate_bar(labels: List[str], rates: List[float], title: str = "Placement Rate by Group", x_title: str = "Group") -> go.Figure:
    """Build bar chart of placement percentages across categorical groupings."""
    if not labels or not rates:
        return _empty_fig(title)

    fig = go.Figure(
        go.Bar(
            x=labels,
            y=rates,
            marker=dict(color=BRAND_COLOR),
            text=[f"{r:.1f}%" for r in rates],
            textposition="auto",
        )
    )
    fig.update_layout(
        title=title,
        height=320,
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(title=x_title),
        yaxis=dict(title="Placement Rate (%)", range=[0, 105]),
    )
    return fig
