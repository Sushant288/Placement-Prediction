"""Module 3: Recommendation Engine.

Provides tailored recommendations, roadmaps, and priority areas to bridge identified gaps.
"""

from typing import List, Dict, Any


def generate_recommendations(gap_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
    """Produce actionable advice based on candidate gaps."""
    recommendations = []
    gaps = gap_analysis.get("gaps", {})
    
    for metric, details in gaps.items():
        if details.get("gap", 0) > 0:
            if "coding_score" in metric:
                recommendations.append({
                    "priority": "High",
                    "category": "Coding & DSA",
                    "action": "Practice LeetCode / HackerRank problems regularly and focus on Core Algorithms.",
                })
            elif "projects" in metric:
                recommendations.append({
                    "priority": "Medium",
                    "category": "Projects",
                    "action": "Build 1-2 end-to-end applications demonstrating domain depth and deploy them.",
                })
            elif "internships" in metric:
                recommendations.append({
                    "priority": "High",
                    "category": "Internships",
                    "action": "Apply for summer internships or contribute to open-source initiatives.",
                })
            elif "communication_score" in metric:
                recommendations.append({
                    "priority": "Medium",
                    "category": "Soft Skills",
                    "action": "Participate in mock interviews, presentation clubs, and group discussions.",
                })
                
    return recommendations
