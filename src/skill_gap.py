"""Module 3: Skill Gap Analysis.

Compares a student profile against industry role benchmarks to identify critical gaps.
"""

from typing import Dict, Any
from src.config import ROLE_REQUIREMENTS


def analyze_skill_gap(student_profile: Dict[str, Any], target_role: str) -> Dict[str, Any]:
    """Calculate deficiencies between student stats and target role expectations."""
    benchmarks = ROLE_REQUIREMENTS.get(target_role, {})
    gaps = {}
    
    for metric, threshold in benchmarks.items():
        user_val = student_profile.get(metric.replace("min_", ""), 0)
        gap = max(0.0, threshold - user_val)
        gaps[metric] = {
            "required": threshold,
            "current": user_val,
            "gap": round(gap, 2),
            "status": "Met" if gap == 0 else "Needs Improvement",
        }
        
    return {
        "role": target_role,
        "gaps": gaps,
    }
