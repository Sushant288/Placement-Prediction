"""Module 3: Skill Gap Analysis Engine.

Evaluates student skill proficiencies and profile metrics against role-specific
benchmarks using transparent, deterministic rules.
"""

import copy
from typing import Any, Dict, List, Optional, Union

from backend.config import (
    DEFAULT_ROLE,
    FEATURE_LABELS,
    FEATURE_RANGES,
    MODERATE_MAX_GAP,
    PROFILE_MAX_BACKLOGS,
    RAW_FEATURES,
    ROLE_PROFILES,
    SAMPLE_STUDENT,
    SKILL_COLS,
    STATUS_GOOD,
    STATUS_MODERATE,
    STATUS_WEAK,
)
from backend.preprocessing import preprocess_input


def _clean_student(student: Dict[str, Any]) -> Dict[str, Union[int, float]]:
    """Validate, clip, and extract clean raw feature values for a candidate."""
    student_copy = dict(student)
    df = preprocess_input(student_copy)
    cleaned: Dict[str, Union[int, float]] = {}
    for col in RAW_FEATURES:
        val = df[col].iloc[0]
        col_type = FEATURE_RANGES[col][2]
        if col_type == "int":
            cleaned[col] = int(round(val))
        else:
            cleaned[col] = float(val)
    return cleaned


def _resolve_role(role: Optional[str]) -> str:
    """Validate and resolve target professional role against configured catalog."""
    if role is None:
        return DEFAULT_ROLE
    if role not in ROLE_PROFILES:
        raise ValueError(
            f"Unknown role '{role}'. Valid roles: {list(ROLE_PROFILES.keys())}"
        )
    return role


def list_roles() -> List[str]:
    """Return available career role names in canonical configuration order."""
    return list(ROLE_PROFILES.keys())


def get_role_profile(role: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve deep copy of role specifications, skill benchmarks, and profile requirements."""
    role_name = _resolve_role(role)
    profile = copy.deepcopy(ROLE_PROFILES[role_name])
    profile["role"] = role_name
    return profile


def get_skill_status(score: float, benchmark: float) -> str:
    """Determine role-relative skill proficiency status based on benchmark difference."""
    gap = benchmark - score
    if gap <= 0:
        return STATUS_GOOD
    elif gap <= MODERATE_MAX_GAP:
        return STATUS_MODERATE
    else:
        return STATUS_WEAK


def analyze_skills(
    student: Dict[str, float], role: Optional[str] = None
) -> Dict[str, Any]:
    """Perform comprehensive role-relative skill and academic profile assessment."""
    cleaned = _clean_student(student)
    role_name = _resolve_role(role)
    profile = ROLE_PROFILES[role_name]
    benchmarks = profile["skill_benchmarks"]
    importance = profile["skill_importance"]
    requirements = profile["profile_requirements"]

    skill_status: Dict[str, Dict[str, Any]] = {}
    priority_candidates: List[Dict[str, Any]] = []
    strengths_candidates: List[Dict[str, Any]] = []
    counts: Dict[str, int] = {
        STATUS_GOOD: 0,
        STATUS_MODERATE: 0,
        STATUS_WEAK: 0,
    }

    weighted_fit_sum = 0.0
    total_importance = 0.0

    for idx, skill in enumerate(SKILL_COLS):
        score = float(cleaned[skill])
        bench = float(benchmarks[skill])
        imp = float(importance[skill])

        gap = max(bench - score, 0.0)
        surplus = max(score - bench, 0.0)
        status = get_skill_status(score, bench)
        counts[status] += 1

        priority_score = round(gap * imp, 2)
        label = FEATURE_LABELS[skill]

        skill_status[skill] = {
            "label": label,
            "score": score,
            "benchmark": bench,
            "gap": round(gap, 2),
            "surplus": round(surplus, 2),
            "status": status,
            "importance": imp,
            "priority_score": priority_score,
        }

        ratio = min(score / bench, 1.0) if bench > 0 else 1.0
        weighted_fit_sum += imp * ratio
        total_importance += imp

        if gap > 0:
            priority_candidates.append({
                "skill": skill,
                "label": label,
                "score": score,
                "benchmark": bench,
                "gap": round(gap, 2),
                "status": status,
                "importance": imp,
                "priority_score": priority_score,
                "_order": idx,
            })
        else:
            strengths_candidates.append({
                "skill": skill,
                "surplus": surplus,
                "_order": idx,
            })

    # Sort priority list: priority_score desc, importance desc, SKILL_COLS order
    priority_candidates.sort(
        key=lambda item: (
            -item["priority_score"],
            -item["importance"],
            item["_order"],
        )
    )
    priority_list: List[Dict[str, Any]] = []
    for rank_idx, item in enumerate(priority_candidates, start=1):
        priority_list.append({
            "rank": rank_idx,
            "skill": item["skill"],
            "label": item["label"],
            "score": item["score"],
            "benchmark": item["benchmark"],
            "gap": item["gap"],
            "status": item["status"],
            "priority_score": item["priority_score"],
        })

    # Sort strengths: surplus desc, SKILL_COLS order
    strengths_candidates.sort(
        key=lambda item: (-item["surplus"], item["_order"])
    )
    strengths: List[str] = [item["skill"] for item in strengths_candidates]

    role_fit_pct = (
        round(100.0 * (weighted_fit_sum / total_importance), 1)
        if total_importance > 0
        else 0.0
    )

    # Evaluate profile requirements
    profile_status: Dict[str, Dict[str, Any]] = {}
    profile_keys = [
        "projects",
        "internships",
        "certifications",
        "cgpa",
        "attendance",
        "backlogs",
    ]
    for key in profile_keys:
        curr_val = cleaned[key]
        if key == "backlogs":
            target_val = PROFILE_MAX_BACKLOGS
            met = bool(curr_val <= target_val)
        else:
            target_val = requirements[key]
            met = bool(curr_val >= target_val)

        profile_status[key] = {
            "label": FEATURE_LABELS[key],
            "current": curr_val,
            "target": target_val,
            "met": met,
        }

    return {
        "role": role_name,
        "skill_status": skill_status,
        "priority_list": priority_list,
        "strengths": strengths,
        "counts": counts,
        "role_fit_pct": role_fit_pct,
        "profile_status": profile_status,
    }


def get_improvement_targets(
    student: Dict[str, float], role: Optional[str] = None
) -> Dict[str, Union[int, float]]:
    """Determine concrete numerical target values for all deficient skills and profile areas."""
    analysis = analyze_skills(student, role)
    role_name = analysis["role"]
    benchmarks = ROLE_PROFILES[role_name]["skill_benchmarks"]
    requirements = ROLE_PROFILES[role_name]["profile_requirements"]
    cleaned = _clean_student(student)

    targets: Dict[str, Union[int, float]] = {}

    # Skills short of benchmark
    for skill in SKILL_COLS:
        if analysis["skill_status"][skill]["gap"] > 0:
            bench_val = benchmarks[skill]
            max_limit = FEATURE_RANGES[skill][1]
            targets[skill] = min(bench_val, max_limit)

    # Profile requirements
    for key, req_val in requirements.items():
        if cleaned[key] < req_val:
            max_limit = FEATURE_RANGES[key][1]
            targets[key] = min(req_val, max_limit)

    # Backlogs
    if cleaned["backlogs"] > PROFILE_MAX_BACKLOGS:
        targets["backlogs"] = PROFILE_MAX_BACKLOGS

    return targets


def get_radar_data(
    student: Dict[str, float], role: Optional[str] = None
) -> Dict[str, Any]:
    """Package skill gap evaluations into a structured radar chart payload."""
    cleaned = _clean_student(student)
    role_name = _resolve_role(role)
    benchmarks = ROLE_PROFILES[role_name]["skill_benchmarks"]

    labels = [FEATURE_LABELS[skill] for skill in SKILL_COLS]
    student_vals = [float(cleaned[skill]) for skill in SKILL_COLS]
    bench_vals = [float(benchmarks[skill]) for skill in SKILL_COLS]

    return {
        "labels": labels,
        "skills": list(SKILL_COLS),
        "student": student_vals,
        "benchmark": bench_vals,
        "max_value": 10,
    }


if __name__ == "__main__":
    report = analyze_skills(SAMPLE_STUDENT)
    role_name = report["role"]

    print("=" * 46)
    print(f" SKILL GAP ANALYSIS - {role_name}")
    print("=" * 46)
    print(f"Role fit: {report['role_fit_pct']}%")
    print(f"{'Skill':<16} {'Score':>6} {'Target':>7} {'Gap':>5} {'Status':>10}")
    print("-" * 46)
    for s in SKILL_COLS:
        st = report["skill_status"][s]
        print(
            f"{st['label']:<16} {int(st['score']):>6} {int(st['benchmark']):>7} "
            f"{int(st['gap']):>5} {st['status']:>10}"
        )
    print("-" * 46)

    priority_strs = [
        f"{item['label']} ({item['priority_score']:.1f})"
        for item in report["priority_list"]
    ]
    print("Priority order: " + (", ".join(priority_strs) if priority_strs else "None"))

    strength_labels = [
        FEATURE_LABELS[s] for s in report["strengths"]
    ]
    print("Strengths: " + (", ".join(strength_labels) if strength_labels else "None"))

    profile_checks = []
    for k, v in report["profile_status"].items():
        status_txt = "met" if v["met"] else "not met"
        profile_checks.append(f"{k} {v['current']}/{v['target']} ({status_txt})")
    print("Profile checks: " + ", ".join(profile_checks))
