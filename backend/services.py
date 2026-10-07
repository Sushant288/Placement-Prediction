"""Module 4: Service Layer.

Provides unified, pure Python interfaces for the Streamlit frontend.
Connects configuration, preprocessing, predictions, skill gap analysis, and recommendations.
"""

import copy
import csv
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

import backend.config as cfg
from backend.config import (
    ACCENT_COLOR,
    APP_ICON,
    APP_SUBTITLE,
    APP_TITLE,
    BRAND_COLOR,
    CGPA_BANDS,
    CLEAN_DATA_PATH,
    CUSTOM_PROFILE_LABEL,
    DEFAULT_ROLE,
    DISCLAIMER_TEXT,
    EXAMPLE_STUDENTS,
    FEATURE_HELP,
    FEATURE_LABELS,
    FEATURE_RANGES,
    FIGURES_DIR,
    INPUT_GROUPS,
    INSIGHT_FIGURE_LIMIT,
    METRICS_PATH,
    PEER_FEATURES,
    PLACEMENT_MODEL_PATH,
    RAW_DATA_PATH,
    RAW_FEATURES,
    RISK_COLORS,
    RISK_LOW_THRESHOLD,
    RISK_MEDIUM_THRESHOLD,
    ROLE_PROFILES,
    SALARY_HIST_BINS,
    SALARY_MODEL_PATH,
    SAMPLE_STUDENT,
    SEVERITY_COLORS,
    SKILL_COLS,
    STATUS_COLORS,
    TAB_NAMES,
    WHATIF_FEATURES,
)
from backend.predict import (
    get_feature_importance,
    get_model_metrics,
    predict_student,
)
from backend.preprocessing import load_clean_data
from backend.recommender import (
    compute_impact_analysis,
    get_recommendations,
    simulate_improvement,
    simulate_reaching_benchmark,
)
from backend.skill_gap import (
    _clean_student,
    _resolve_role,
    analyze_skills,
    get_radar_data,
)

# Module-level caches
_CLEAN_DF_CACHE: Optional[pd.DataFrame] = None
_DATASET_INSIGHTS_CACHE: Optional[Dict[str, Any]] = None


def clear_caches() -> None:
    """Clear cached clean DataFrame and dataset statistics."""
    global _CLEAN_DF_CACHE, _DATASET_INSIGHTS_CACHE
    _CLEAN_DF_CACHE = None
    _DATASET_INSIGHTS_CACHE = None


def _get_clean_df() -> pd.DataFrame:
    """Retrieve or lazily cache the clean dataset DataFrame."""
    global _CLEAN_DF_CACHE
    if _CLEAN_DF_CACHE is None:
        if not cfg.CLEAN_DATA_PATH.exists():
            raise FileNotFoundError(
                f"Clean dataset not found at {cfg.CLEAN_DATA_PATH}. Run: python -m backend.preprocessing"
            )
        _CLEAN_DF_CACHE = load_clean_data()
    return _CLEAN_DF_CACHE


def get_app_status() -> Dict[str, Any]:
    """Verify presence of core artifacts and supply remediation commands."""
    missing: List[str] = []
    if not cfg.PLACEMENT_MODEL_PATH.exists():
        missing.append("placement_model.pkl")
    if not cfg.SALARY_MODEL_PATH.exists():
        missing.append("salary_model.pkl")
    if not cfg.METRICS_PATH.exists():
        missing.append("metrics.json")
    if not cfg.CLEAN_DATA_PATH.exists():
        missing.append("clean_data.csv")

    fix_commands: List[str] = []
    if not cfg.CLEAN_DATA_PATH.exists():
        if not cfg.RAW_DATA_PATH.exists():
            fix_commands.append("python -m backend.data_generator")
        fix_commands.append("python -m backend.preprocessing")

    needs_models = (
        not cfg.PLACEMENT_MODEL_PATH.exists()
        or not cfg.SALARY_MODEL_PATH.exists()
        or not cfg.METRICS_PATH.exists()
    )
    if needs_models:
        if "python -m backend.preprocessing" not in fix_commands and not cfg.CLEAN_DATA_PATH.exists():
            fix_commands.append("python -m backend.preprocessing")
        fix_commands.append("python -m backend.train_models")

    # Deduplicate while preserving order
    seen = set()
    ordered_fixes = []
    for cmd in fix_commands:
        if cmd not in seen:
            seen.add(cmd)
            ordered_fixes.append(cmd)

    return {
        "ready": len(missing) == 0,
        "missing": missing,
        "fix_commands": ordered_fixes,
    }


def get_ui_config() -> Dict[str, Any]:
    """Provide UI branding tokens, color palettes, and labels."""
    return {
        "app_title": APP_TITLE,
        "app_subtitle": APP_SUBTITLE,
        "app_icon": APP_ICON,
        "disclaimer": DISCLAIMER_TEXT,
        "tab_names": list(TAB_NAMES),
        "status_colors": dict(STATUS_COLORS),
        "risk_colors": dict(RISK_COLORS),
        "severity_colors": dict(SEVERITY_COLORS),
        "brand_color": BRAND_COLOR,
        "accent_color": ACCENT_COLOR,
        "risk_low_pct": float(RISK_LOW_THRESHOLD * 100.0),
        "risk_medium_pct": float(RISK_MEDIUM_THRESHOLD * 100.0),
        "whatif_features": list(WHATIF_FEATURES),
        "feature_labels": dict(FEATURE_LABELS),
        "custom_profile_label": CUSTOM_PROFILE_LABEL,
    }


def get_input_spec() -> List[Dict[str, Any]]:
    """Generate form specifications for all raw feature inputs in group order."""
    spec: List[Dict[str, Any]] = []
    for group_name, cols in INPUT_GROUPS.items():
        for col in cols:
            min_v, max_v, col_type = FEATURE_RANGES[col]
            is_int = col_type == "int"
            spec.append({
                "key": col,
                "label": FEATURE_LABELS[col],
                "group": group_name,
                "type": col_type,
                "min": int(min_v) if is_int else float(min_v),
                "max": int(max_v) if is_int else float(max_v),
                "step": 1 if is_int else 0.1,
                "default": int(SAMPLE_STUDENT[col]) if is_int else float(SAMPLE_STUDENT[col]),
                "help": FEATURE_HELP.get(col, ""),
            })
    return spec


def get_example_students() -> Dict[str, Dict[str, float]]:
    """Return isolated copies of reference student profiles."""
    return copy.deepcopy(EXAMPLE_STUDENTS)


def get_roles() -> List[Dict[str, str]]:
    """Return available career profiles and descriptions."""
    return [
        {"name": name, "description": data["description"]}
        for name, data in ROLE_PROFILES.items()
    ]


def get_full_report(
    student: Dict[str, float], role: Optional[str] = None
) -> Dict[str, Any]:
    """Assemble end-to-end analytics report for a candidate and role."""
    resolved_role = _resolve_role(role)
    cleaned = _clean_student(student)

    # Predictions
    pred = predict_student(cleaned)

    # Skill gap analysis
    skills = analyze_skills(cleaned, resolved_role)
    radar = get_radar_data(cleaned, resolved_role)

    # Impact analysis (computed once)
    impact = compute_impact_analysis(cleaned, resolved_role)
    impact_map = {item["area"]: item["gain_pct"] for item in impact}

    # Recommendations filled with impact
    recs = get_recommendations(cleaned, resolved_role, include_impact=False)
    for r in recs:
        r["expected_gain_pct"] = impact_map.get(r["area"])

    # Benchmark simulation
    bench_sim = simulate_reaching_benchmark(cleaned, resolved_role)

    # Role comparison across all available roles
    role_comp: List[Dict[str, Any]] = []
    for r_name in ROLE_PROFILES.keys():
        an = analyze_skills(cleaned, r_name)
        role_comp.append({
            "role": r_name,
            "role_fit_pct": float(an["role_fit_pct"]),
            "weak_count": int(an["counts"]["WEAK"]),
            "moderate_count": int(an["counts"]["MODERATE"]),
            "is_selected": bool(r_name == resolved_role),
        })
    role_comp.sort(key=lambda x: -x["role_fit_pct"])

    # Peer percentiles from clean data if accessible
    peer: Optional[Dict[str, Dict[str, Any]]] = None
    try:
        clean_df = _get_clean_df()
        peer = {}
        for feat in PEER_FEATURES:
            if feat == "cgpa":
                val = float(cleaned["cgpa"])
            else:
                val = float(pred["engineered_scores"][feat])
            pct = round(float((clean_df[feat] <= val).mean() * 100.0), 1)
            peer[feat] = {
                "label": FEATURE_LABELS.get(feat, feat.replace("_", " ").title()),
                "percentile": pct,
            }
    except Exception:
        peer = None

    # Headline
    risk = pred["risk_level"]
    if risk == "LOW":
        outlook = "STRONG"
    elif risk == "MEDIUM":
        outlook = "MODERATE"
    else:
        outlook = "NEEDS WORK"

    headline = (
        f"Placement outlook: {outlook}. {pred['probability_pct']}% probability, "
        f"readiness {pred['readiness_score']}/100, risk {risk}."
    )

    return {
        "role": resolved_role,
        "role_description": ROLE_PROFILES[resolved_role]["description"],
        "student": cleaned,
        "prediction": pred,
        "skills": skills,
        "radar": radar,
        "impact": impact,
        "recommendations": recs,
        "benchmark_simulation": bench_sim,
        "role_comparison": role_comp,
        "peer": peer,
        "headline": headline,
        "disclaimer": DISCLAIMER_TEXT,
    }


def run_what_if(
    student: Dict[str, float],
    changes: Dict[str, float],
    role: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute what-if simulation and quantify role fit and risk transitions."""
    resolved_role = _resolve_role(role)
    cleaned = _clean_student(student)

    skills_before = analyze_skills(cleaned, resolved_role)
    fit_before = float(skills_before["role_fit_pct"])
    counts_before = {k: int(v) for k, v in skills_before["counts"].items()}

    sim = simulate_improvement(cleaned, changes)

    skills_after = analyze_skills(sim["improved_student"], resolved_role)
    fit_after = float(skills_after["role_fit_pct"])
    counts_after = {k: int(v) for k, v in skills_after["counts"].items()}

    risk_changed = bool(sim["before"]["risk_level"] != sim["after"]["risk_level"])

    return {
        "simulation": sim,
        "role": resolved_role,
        "role_fit_before": fit_before,
        "role_fit_after": fit_after,
        "counts_before": counts_before,
        "counts_after": counts_after,
        "risk_changed": risk_changed,
    }


def get_dataset_insights() -> Dict[str, Any]:
    """Compute aggregate statistical insights from clean placement dataset."""
    global _DATASET_INSIGHTS_CACHE
    if _DATASET_INSIGHTS_CACHE is not None:
        return _DATASET_INSIGHTS_CACHE

    df = _get_clean_df()
    n_students = int(len(df))
    placed_mask = df["placed"] == 1
    placed_count = int(placed_mask.sum())
    not_placed_count = n_students - placed_count
    placement_rate_pct = round(float(placed_count / n_students * 100.0), 1)

    placed_salaries = df.loc[placed_mask, "salary_lpa"]
    salary_stats = {
        "mean": round(float(placed_salaries.mean()), 1),
        "median": round(float(placed_salaries.median()), 1),
        "p90": round(float(np.percentile(placed_salaries, 90)), 1),
        "min": round(float(placed_salaries.min()), 1),
        "max": round(float(placed_salaries.max()), 1),
    }

    counts, bin_edges = np.histogram(placed_salaries, bins=SALARY_HIST_BINS)
    salary_hist = {
        "bin_edges": [round(float(b), 2) for b in bin_edges],
        "counts": [int(c) for c in counts],
    }

    # Skill means placed vs not placed
    skill_labels = [FEATURE_LABELS[s] for s in SKILL_COLS]
    skill_means_placed = [round(float(df.loc[placed_mask, s].mean()), 2) for s in SKILL_COLS]
    skill_means_unplaced = [round(float(df.loc[~placed_mask, s].mean()), 2) for s in SKILL_COLS]
    skill_means = {
        "labels": skill_labels,
        "placed": skill_means_placed,
        "not_placed": skill_means_unplaced,
    }

    # Profile means
    prof_cols = ["cgpa", "backlogs", "projects", "internships", "certifications"]
    prof_labels = [FEATURE_LABELS[c] for c in prof_cols]
    prof_means_placed = [round(float(df.loc[placed_mask, c].mean()), 2) for c in prof_cols]
    prof_means_unplaced = [round(float(df.loc[~placed_mask, c].mean()), 2) for c in prof_cols]
    profile_means = {
        "labels": prof_labels,
        "placed": prof_means_placed,
        "not_placed": prof_means_unplaced,
    }

    # Placement rate by internships
    intern_vals = sorted(df["internships"].unique())
    intern_labels = [f"{int(v)} Internships" if v != 1 else "1 Internship" for v in intern_vals]
    intern_rates = [
        round(float((df.loc[df["internships"] == v, "placed"] == 1).mean() * 100.0), 1)
        for v in intern_vals
    ]
    rate_by_intern = {
        "labels": intern_labels,
        "rates": intern_rates,
    }

    # Placement rate by CGPA band
    band_labels: List[str] = []
    band_rates: List[float] = []
    for low, high, label in CGPA_BANDS:
        sub = df[(df["cgpa"] >= low) & (df["cgpa"] < high)]
        if len(sub) > 0:
            band_labels.append(label)
            band_rates.append(round(float((sub["placed"] == 1).mean() * 100.0), 1))
    rate_by_cgpa = {
        "labels": band_labels,
        "rates": band_rates,
    }

    insights: Dict[str, Any] = {
        "n_students": n_students,
        "placed_count": placed_count,
        "not_placed_count": not_placed_count,
        "placement_rate_pct": placement_rate_pct,
        "salary_stats": salary_stats,
        "salary_hist": salary_hist,
        "skill_means": skill_means,
        "profile_means": profile_means,
        "placement_rate_by_internships": rate_by_intern,
        "placement_rate_by_cgpa_band": rate_by_cgpa,
    }

    _DATASET_INSIGHTS_CACHE = insights
    return insights


def get_model_insights() -> Dict[str, Any]:
    """Retrieve model evaluation tables, permutation importances, and figure links."""
    metrics = get_model_metrics()
    meta = metrics.get("meta", {})
    clf_data = metrics.get("classifier", {})
    reg_data = metrics.get("regressor", {})

    best_clf = clf_data.get("best_model", "")
    clf_rows: List[Dict[str, Any]] = []
    for m_name, m_info in clf_data.get("models", {}).items():
        t = m_info.get("test", {})
        clf_rows.append({
            "model": m_name,
            "cv_roc_auc": round(float(m_info.get("cv_roc_auc", 0.0)), 4),
            "accuracy": round(float(t.get("accuracy", 0.0)), 4),
            "precision": round(float(t.get("precision", 0.0)), 4),
            "recall": round(float(t.get("recall", 0.0)), 4),
            "f1": round(float(t.get("f1", 0.0)), 4),
            "roc_auc": round(float(t.get("roc_auc", 0.0)), 4),
            "brier": round(float(t.get("brier_score", 0.0)), 4),
            "is_best": bool(m_name == best_clf),
        })

    best_reg = reg_data.get("best_model", "")
    reg_rows: List[Dict[str, Any]] = []
    for m_name, m_info in reg_data.get("models", {}).items():
        t = m_info.get("test", {})
        reg_rows.append({
            "model": m_name,
            "cv_rmse": round(float(m_info.get("cv_rmse", 0.0)), 4),
            "mae": round(float(t.get("mae", 0.0)), 4),
            "rmse": round(float(t.get("rmse", 0.0)), 4),
            "r2": round(float(t.get("r2", 0.0)), 4),
            "is_best": bool(m_name == best_reg),
        })

    clf_imp_raw = get_feature_importance("classifier", top_n=12)
    reg_imp_raw = get_feature_importance("regressor", top_n=12)

    readable_label = lambda f: FEATURE_LABELS.get(f, f.replace("_", " ").title())
    clf_imp = {readable_label(k): round(float(v), 4) for k, v in clf_imp_raw.items()}
    reg_imp = {readable_label(k): round(float(v), 4) for k, v in reg_imp_raw.items()}

    # Collect figures
    figure_list: List[Dict[str, str]] = []
    if cfg.FIGURES_DIR.exists():
        png_files = sorted(cfg.FIGURES_DIR.glob("*.png"))
        for p in png_files[: cfg.INSIGHT_FIGURE_LIMIT]:
            title = p.stem.replace("_", " ").title()
            figure_list.append({"title": title, "path": str(p)})

    return {
        "meta": {
            "n_train": int(meta.get("n_train", 0)),
            "n_test": int(meta.get("n_test", 0)),
            "trained_at": str(meta.get("trained_at", "")),
            "sklearn_version": str(meta.get("sklearn_version", "")),
        },
        "classifier": {
            "best_model": best_clf,
            "selection_reason": str(clf_data.get("selection_reason", "")),
            "baseline_brier": round(float(clf_data.get("baseline_brier", 0.0)), 4),
            "rows": clf_rows,
        },
        "regressor": {
            "best_model": best_reg,
            "baseline_rmse": round(float(reg_data.get("baseline_rmse", 0.0)), 4),
            "n_rows_train": int(reg_data.get("n_train_rows", 0)),
            "n_rows_test": int(reg_data.get("n_test_rows", 0)),
            "rows": reg_rows,
        },
        "feature_importance": {
            "classifier": clf_imp,
            "regressor": reg_imp,
        },
        "figures": figure_list,
    }


def build_report_markdown(report: Dict[str, Any]) -> str:
    """Generate complete downloadable Markdown dossier."""
    pred = report["prediction"]
    sal_rng = pred["salary_range"]
    lines: List[str] = []

    lines.append(f"# {APP_TITLE} - Candidate Evaluation Dossier")
    lines.append(f"**Target Role:** {report['role']}")
    lines.append(f"**Executive Headline:** {report['headline']}\n")

    lines.append("## 1. Outcome Projections")
    lines.append("| Metric | Value | Reference / Status |")
    lines.append("| :--- | :--- | :--- |")
    lines.append(f"| Placement Probability | {pred['probability_pct']}% | Risk Level: {pred['risk_level']} |")
    lines.append(f"| Readiness Score | {pred['readiness_score']} / 100 | Target: 75+ |")
    lines.append(f"| Expected Package (if placed) | {sal_rng['label']} | Point Estimate: {pred['salary_estimate']} LPA |")
    lines.append(f"| Role Alignment Fit | {report['skills']['role_fit_pct']}% | Canonical Benchmark Match |")
    lines.append("")

    lines.append("## 2. Skill Gap Breakdown")
    lines.append("| Skill | Current Score | Benchmark Target | Gap | Status |")
    lines.append("| :--- | :---: | :---: | :---: | :---: |")
    for s in SKILL_COLS:
        st = report["skills"]["skill_status"][s]
        lines.append(
            f"| {st['label']} | {st['score']} | {st['benchmark']} | {st['gap']} | {st['status']} |"
        )
    lines.append("")

    lines.append("## 3. Prioritized Strategic Recommendations")
    recs = report["recommendations"]
    if recs:
        for r in recs:
            gain_txt = (
                f"(Expected Gain: +{r['expected_gain_pct']}%)"
                if r["expected_gain_pct"] is not None
                else ""
            )
            curr_tgt = (
                f" [Current: {r['current']} -> Target: {r['target']}]"
                if r["current"] is not None and r["target"] is not None
                else ""
            )
            lines.append(
                f"{r['rank']}. **[{r['severity']}] {r['label']}** {gain_txt}{curr_tgt}\n   - {r['action']}"
            )
    else:
        lines.append("- No immediate interventions required. Profile matches or exceeds benchmarks.")
    lines.append("")

    sim = report["benchmark_simulation"]
    lines.append("## 4. Benchmark Simulation")
    lines.append(f"**Simulated Outcome:** {sim['summary']}\n")

    lines.append("## 5. Regulatory Disclaimer")
    lines.append(f"> {report['disclaimer']}")

    return "\n".join(lines)


def build_report_csv(report: Dict[str, Any]) -> str:
    """Generate single-row comma-separated analysis summary."""
    cleaned = report["student"]
    pred = report["prediction"]
    sal_rng = pred["salary_range"]
    recs = report["recommendations"]

    top_recs = [r["label"] for r in recs[:3] if r.get("label")]
    top_recs_str = " | ".join(top_recs) if top_recs else "Maintain Benchmark"

    fieldnames = [
        "role",
        *RAW_FEATURES,
        "probability_pct",
        "readiness_score",
        "salary_low",
        "salary_high",
        "risk_level",
        "role_fit_pct",
        "top_recommendations",
    ]

    row_dict: Dict[str, Any] = {
        "role": report["role"],
        **{k: cleaned[k] for k in RAW_FEATURES},
        "probability_pct": pred["probability_pct"],
        "readiness_score": pred["readiness_score"],
        "salary_low": sal_rng["low"],
        "salary_high": sal_rng["high"],
        "risk_level": pred["risk_level"],
        "role_fit_pct": report["skills"]["role_fit_pct"],
        "top_recommendations": top_recs_str,
    }

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerow(row_dict)
    return output.getvalue()
