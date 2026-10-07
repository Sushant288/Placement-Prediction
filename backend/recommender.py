"""Module 3: Recommendation Engine and What-If Simulator.

Generates targeted action items based on skill gap and profile deficiencies,
quantifies single-intervention placement impact, and simulates profile improvements.
"""

from typing import Any, Dict, List, Optional, Union

import numpy as np

from backend.config import (
    DEFAULT_ROLE,
    FEATURE_LABELS,
    FEATURE_RANGES,
    MAINTAIN_MESSAGE,
    PROFILE_ACTIONS,
    PROFILE_MAX_BACKLOGS,
    PROFILE_RULE_WEIGHTS,
    PROJECTS_HIGH_SHORTFALL,
    RAW_FEATURES,
    ROLE_PROFILES,
    SAMPLE_STUDENT,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    SEVERITY_ORDER,
    SKILL_ACTIONS,
    SKILL_COLS,
    SKILL_SEVERITY,
    STATUS_GOOD,
)
from backend.predict import predict_student
from backend.skill_gap import (
    _clean_student,
    _resolve_role,
    analyze_skills,
    get_improvement_targets,
)


def compute_impact_analysis(
    student: Dict[str, float], role: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Simulate placement probability impact for individual deficient features."""
    cleaned = _clean_student(student)
    targets = get_improvement_targets(cleaned, role)

    if not targets:
        return []

    base_prediction = predict_student(cleaned)
    prob_before_pct = float(base_prediction["probability_pct"])

    impact_items: List[Dict[str, Any]] = []

    for feature, target_val in targets.items():
        curr_val = cleaned[feature]
        mod_student = dict(cleaned)
        mod_student[feature] = target_val

        after_prediction = predict_student(mod_student)
        prob_after_pct = float(after_prediction["probability_pct"])
        gain_pct = round(prob_after_pct - prob_before_pct, 1)

        impact_items.append({
            "area": feature,
            "label": FEATURE_LABELS[feature],
            "from": curr_val,
            "to": target_val,
            "probability_before_pct": prob_before_pct,
            "probability_after_pct": prob_after_pct,
            "gain_pct": gain_pct,
        })

    # Sort by gain_pct desc, ties broken by canonical RAW_FEATURES order
    impact_items.sort(
        key=lambda item: (-item["gain_pct"], RAW_FEATURES.index(item["area"]))
    )
    return impact_items


def get_recommendations(
    student: Dict[str, float],
    role: Optional[str] = None,
    max_items: Optional[int] = None,
    include_impact: bool = True,
) -> List[Dict[str, Any]]:
    """Synthesize prioritized, actionable coaching recommendations."""
    cleaned = _clean_student(student)
    analysis = analyze_skills(cleaned, role)
    role_name = analysis["role"]
    requirements = ROLE_PROFILES[role_name]["profile_requirements"]

    candidates: List[Dict[str, Any]] = []

    # 1. Skill recommendations (WEAK and MODERATE only)
    for skill in SKILL_COLS:
        st = analysis["skill_status"][skill]
        status = st["status"]
        if status in (STATUS_GOOD,):
            continue

        severity = SKILL_SEVERITY[status]
        action = SKILL_ACTIONS[skill][status]
        priority_score = float(st["priority_score"])

        candidates.append({
            "category": "skill",
            "area": skill,
            "label": st["label"],
            "severity": severity,
            "current": st["score"],
            "target": st["benchmark"],
            "action": action,
            "priority_score": priority_score,
        })

    # 2. Profile recommendations
    # Projects
    proj_curr = int(cleaned["projects"])
    proj_req = int(requirements["projects"])
    if proj_curr < proj_req:
        proj_shortfall = proj_req - proj_curr
        proj_sev = (
            SEVERITY_HIGH
            if proj_shortfall >= PROJECTS_HIGH_SHORTFALL
            else SEVERITY_MEDIUM
        )
        proj_action = PROFILE_ACTIONS["projects"].format(
            shortfall=proj_shortfall
        )
        candidates.append({
            "category": "experience",
            "area": "projects",
            "label": FEATURE_LABELS["projects"],
            "severity": proj_sev,
            "current": proj_curr,
            "target": proj_req,
            "action": proj_action,
            "priority_score": round(
                proj_shortfall * PROFILE_RULE_WEIGHTS["projects"], 2
            ),
        })

    # Internships
    intern_curr = int(cleaned["internships"])
    intern_req = int(requirements["internships"])
    if intern_curr < intern_req:
        intern_shortfall = intern_req - intern_curr
        intern_sev = SEVERITY_HIGH if intern_curr == 0 else SEVERITY_MEDIUM
        intern_action = PROFILE_ACTIONS["internships"].format(
            shortfall=intern_shortfall
        )
        candidates.append({
            "category": "experience",
            "area": "internships",
            "label": FEATURE_LABELS["internships"],
            "severity": intern_sev,
            "current": intern_curr,
            "target": intern_req,
            "action": intern_action,
            "priority_score": round(
                intern_shortfall * PROFILE_RULE_WEIGHTS["internships"], 2
            ),
        })

    # Certifications
    cert_curr = int(cleaned["certifications"])
    cert_req = int(requirements["certifications"])
    if cert_curr < cert_req:
        cert_shortfall = cert_req - cert_curr
        cert_action = PROFILE_ACTIONS["certifications"].format(
            shortfall=cert_shortfall
        )
        candidates.append({
            "category": "experience",
            "area": "certifications",
            "label": FEATURE_LABELS["certifications"],
            "severity": SEVERITY_LOW,
            "current": cert_curr,
            "target": cert_req,
            "action": cert_action,
            "priority_score": round(
                cert_shortfall * PROFILE_RULE_WEIGHTS["certifications"], 2
            ),
        })

    # Backlogs
    backlogs_curr = int(cleaned["backlogs"])
    if backlogs_curr > PROFILE_MAX_BACKLOGS:
        backlogs_shortfall = backlogs_curr - PROFILE_MAX_BACKLOGS
        backlogs_action = PROFILE_ACTIONS["backlogs"].format(
            current=backlogs_curr
        )
        candidates.append({
            "category": "academic",
            "area": "backlogs",
            "label": FEATURE_LABELS["backlogs"],
            "severity": SEVERITY_HIGH,
            "current": backlogs_curr,
            "target": PROFILE_MAX_BACKLOGS,
            "action": backlogs_action,
            "priority_score": round(
                backlogs_shortfall * PROFILE_RULE_WEIGHTS["backlogs"], 2
            ),
        })

    # CGPA
    cgpa_curr = float(cleaned["cgpa"])
    cgpa_req = float(requirements["cgpa"])
    if cgpa_curr < cgpa_req:
        cgpa_shortfall = round(cgpa_req - cgpa_curr, 2)
        cgpa_action = PROFILE_ACTIONS["cgpa"].format(target=f"{cgpa_req:.1f}")
        candidates.append({
            "category": "academic",
            "area": "cgpa",
            "label": FEATURE_LABELS["cgpa"],
            "severity": SEVERITY_MEDIUM,
            "current": cgpa_curr,
            "target": cgpa_req,
            "action": cgpa_action,
            "priority_score": round(
                cgpa_shortfall * PROFILE_RULE_WEIGHTS["cgpa"], 2
            ),
        })

    # Attendance
    att_curr = int(cleaned["attendance"])
    att_req = int(requirements["attendance"])
    if att_curr < att_req:
        att_shortfall = att_req - att_curr
        att_action = PROFILE_ACTIONS["attendance"].format(target=att_req)
        candidates.append({
            "category": "academic",
            "area": "attendance",
            "label": FEATURE_LABELS["attendance"],
            "severity": SEVERITY_LOW,
            "current": att_curr,
            "target": att_req,
            "action": att_action,
            "priority_score": round(
                att_shortfall * PROFILE_RULE_WEIGHTS["attendance"], 2
            ),
        })

    # If no candidate recommendations exist, return single overall maintain item
    if not candidates:
        return [
            {
                "rank": 1,
                "category": "overall",
                "area": "overall",
                "label": "Overall",
                "severity": SEVERITY_LOW,
                "current": None,
                "target": None,
                "action": MAINTAIN_MESSAGE,
                "priority_score": 0.0,
                "expected_gain_pct": None,
            }
        ]

    # Sort candidates by (SEVERITY_ORDER[severity], -priority_score, area)
    candidates.sort(
        key=lambda item: (
            SEVERITY_ORDER[item["severity"]],
            -item["priority_score"],
            item["area"],
        )
    )

    # Compute impact mapping if requested
    impact_map: Dict[str, float] = {}
    if include_impact:
        impacts = compute_impact_analysis(cleaned, role)
        impact_map = {imp["area"]: imp["gain_pct"] for imp in impacts}

    # Format final items with contiguous rank 1..N and expected_gain_pct
    final_items: List[Dict[str, Any]] = []
    for rank_idx, item in enumerate(candidates, start=1):
        gain_val = (
            impact_map.get(item["area"]) if include_impact else None
        )
        final_items.append({
            "rank": rank_idx,
            "category": item["category"],
            "area": item["area"],
            "label": item["label"],
            "severity": item["severity"],
            "current": item["current"],
            "target": item["target"],
            "action": item["action"],
            "priority_score": item["priority_score"],
            "expected_gain_pct": gain_val,
        })

    if max_items is not None and max_items > 0:
        return final_items[:max_items]

    return final_items


def simulate_improvement(
    student: Dict[str, float], changes: Dict[str, float]
) -> Dict[str, Any]:
    """Simulate user-defined feature modifications and quantify outcomes."""
    # Validate feature names and numeric types in changes
    for feat, val in changes.items():
        if feat not in RAW_FEATURES:
            raise ValueError(
                f"Unknown feature '{feat}'. Valid features: {RAW_FEATURES}"
            )
        if not isinstance(val, (int, float, np.number)) or isinstance(val, bool):
            raise ValueError(
                f"Value for feature '{feat}' must be numeric, got {type(val).__name__} ({val})"
            )

    cleaned_before = _clean_student(student)

    # Apply changes to a clean copy
    mod_student = dict(cleaned_before)
    mod_student.update(changes)
    cleaned_after = _clean_student(mod_student)

    # Identify applied changes where value actually changed post-clipping
    applied_changes: Dict[str, Dict[str, Union[int, float]]] = {}
    for feat in RAW_FEATURES:
        if cleaned_before[feat] != cleaned_after[feat]:
            applied_changes[feat] = {
                "from": cleaned_before[feat],
                "to": cleaned_after[feat],
            }

    pred_before = predict_student(cleaned_before)
    pred_after = predict_student(cleaned_after)

    before_dict = {
        "probability_pct": float(pred_before["probability_pct"]),
        "readiness_score": float(pred_before["readiness_score"]),
        "risk_level": str(pred_before["risk_level"]),
        "salary_estimate": float(pred_before["salary_estimate"]),
        "salary_range_label": str(pred_before["salary_range"]["label"]),
    }
    after_dict = {
        "probability_pct": float(pred_after["probability_pct"]),
        "readiness_score": float(pred_after["readiness_score"]),
        "risk_level": str(pred_after["risk_level"]),
        "salary_estimate": float(pred_after["salary_estimate"]),
        "salary_range_label": str(pred_after["salary_range"]["label"]),
    }

    prob_delta = round(
        after_dict["probability_pct"] - before_dict["probability_pct"], 1
    )
    read_delta = round(
        after_dict["readiness_score"] - before_dict["readiness_score"], 1
    )
    sal_delta = round(
        after_dict["salary_estimate"] - before_dict["salary_estimate"], 1
    )

    delta_dict = {
        "probability_pct": prob_delta,
        "readiness_score": read_delta,
        "salary_estimate": sal_delta,
    }

    sign_str = "+" if prob_delta >= 0 else ""
    summary_str = (
        f"Probability {before_dict['probability_pct']}% -> {after_dict['probability_pct']}% "
        f"({sign_str}{prob_delta:.1f} points), readiness "
        f"{before_dict['readiness_score']} -> {after_dict['readiness_score']}"
    )

    return {
        "before": before_dict,
        "after": after_dict,
        "delta": delta_dict,
        "applied_changes": applied_changes,
        "improved_student": cleaned_after,
        "summary": summary_str,
    }


def simulate_reaching_benchmark(
    student: Dict[str, float],
    role: Optional[str] = None,
    include_profile: bool = False,
) -> Dict[str, Any]:
    """Simulate lifting all deficient skills and requirements to target benchmarks."""
    cleaned = _clean_student(student)
    changes: Dict[str, float] = {}

    if include_profile:
        targets = get_improvement_targets(cleaned, role)
        changes = dict(targets)
    else:
        analysis = analyze_skills(cleaned, role)
        for skill in SKILL_COLS:
            if analysis["skill_status"][skill]["gap"] > 0:
                changes[skill] = analysis["skill_status"][skill]["benchmark"]

    return simulate_improvement(cleaned, changes)


if __name__ == "__main__":
    recs = get_recommendations(SAMPLE_STUDENT, max_items=5)
    impacts = compute_impact_analysis(SAMPLE_STUDENT)

    print("=" * 60)
    print(" TOP RECOMMENDATIONS - SAMPLE STUDENT")
    print("=" * 60)
    for r in recs:
        gain_str = (
            f"+{r['expected_gain_pct']:.1f}%"
            if r["expected_gain_pct"] is not None and r["expected_gain_pct"] >= 0
            else f"{r['expected_gain_pct']}%"
        )
        print(f"[{r['rank']}] {r['severity']:<6} | {r['label']:<16} | Impact: {gain_str}")
        print(f"    Action: {r['action']}")
    print("-" * 60)

    print("\nIMPACT ANALYSIS TABLE:")
    print(f"{'Area':<16} {'From':>6} {'To':>6} {'Before %':>10} {'After %':>10} {'Gain %':>8}")
    print("-" * 60)
    for imp in impacts:
        print(
            f"{imp['label']:<16} {imp['from']:>6} {imp['to']:>6} "
            f"{imp['probability_before_pct']:>10.1f} {imp['probability_after_pct']:>10.1f} "
            f"{imp['gain_pct']:>8.1f}"
        )
    print("-" * 60)

    # What-If Demo: SQL to benchmark (6 for Software Developer)
    sim = simulate_improvement(SAMPLE_STUDENT, {"sql": 6})
    print("\nWHAT-IF SIMULATION (SQL 5 -> 6):")
    print(sim["summary"])
