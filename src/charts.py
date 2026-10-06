"""Module 4: Visualization and Charts.

Generates interactive charts (e.g., Plotly, Matplotlib) for the Streamlit dashboard.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any


def plot_radar_chart(student_profile: Dict[str, Any], role_benchmarks: Dict[str, Any]) -> go.Figure:
    """Create a radar chart comparing student scores to target role benchmarks."""
    categories = ["CGPA (x10)", "Coding Score", "Communication Score", "Projects (x20)", "Internships (x25)"]
    
    student_vals = [
        student_profile.get("cgpa", 0) * 10,
        student_profile.get("coding_score", 0),
        student_profile.get("communication_score", 0),
        student_profile.get("projects", 0) * 20,
        student_profile.get("internships", 0) * 25,
    ]
    
    benchmark_vals = [
        role_benchmarks.get("min_cgpa", 0) * 10,
        role_benchmarks.get("min_coding_score", 0),
        role_benchmarks.get("min_communication_score", 0),
        role_benchmarks.get("min_projects", 0) * 20,
        role_benchmarks.get("min_internships", 0) * 25,
    ]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=student_vals,
        theta=categories,
        fill="toself",
        name="Candidate"
    ))
    fig.add_trace(go.Scatterpolar(
        r=benchmark_vals,
        theta=categories,
        fill="toself",
        name="Benchmark"
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        template="plotly_dark",
    )
    return fig


def plot_feature_importance(importance_df: pd.DataFrame) -> go.Figure:
    """Plot horizontal bar chart of feature importances."""
    fig = px.bar(
        importance_df,
        x="importance",
        y="feature",
        orientation="h",
        title="Feature Importance",
        template="plotly_dark",
    )
    return fig
