"""Configuration settings and schema definitions for the Placement Prediction system."""

from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

# ==========================================================
# A) PATHS
# ==========================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "placement_data.csv"
CLEAN_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "clean_data.csv"
TRAIN_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "train.csv"
TEST_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "test.csv"

MODELS_DIR = PROJECT_ROOT / "models"
PLACEMENT_MODEL_PATH = MODELS_DIR / "placement_model.pkl"
SALARY_MODEL_PATH = MODELS_DIR / "salary_model.pkl"
METRICS_PATH = MODELS_DIR / "metrics.json"

FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"


# ==========================================================
# B) GENERAL SETTINGS
# ==========================================================
RANDOM_SEED = 42
N_STUDENTS = 2500
TEST_SIZE = 0.2
TARGET_PLACEMENT_RATE = 0.68
INJECT_MISSING = True
MISSING_RATE = 0.015
MISSING_COLUMNS = ["attendance", "certifications", "communication"]


# ==========================================================
# C) SCHEMA
# ==========================================================
FEATURE_RANGES: Dict[str, Tuple[Union[int, float], Union[int, float], str]] = {
    "cgpa": (5.0, 10.0, "float"),
    "backlogs": (0, 5, "int"),
    "attendance": (50, 100, "int"),
    "internships": (0, 3, "int"),
    "projects": (0, 6, "int"),
    "certifications": (0, 5, "int"),
    "dsa": (1, 10, "int"),
    "programming": (1, 10, "int"),
    "sql": (1, 10, "int"),
    "cloud": (1, 10, "int"),
    "web": (1, 10, "int"),
    "communication": (1, 10, "int"),
    "aptitude": (1, 10, "int"),
}

ACADEMIC_COLS: List[str] = ["cgpa", "backlogs", "attendance"]
TECH_SKILL_COLS: List[str] = ["dsa", "programming", "sql", "cloud", "web"]
SOFT_SKILL_COLS: List[str] = ["communication", "aptitude"]
EXPERIENCE_COLS: List[str] = ["internships", "projects", "certifications"]

RAW_FEATURES: List[str] = (
    ACADEMIC_COLS + EXPERIENCE_COLS + TECH_SKILL_COLS + SOFT_SKILL_COLS
)
ENGINEERED_FEATURES: List[str] = [
    "tech_score",
    "soft_score",
    "experience_score",
    "academic_score",
]
MODEL_FEATURES: List[str] = RAW_FEATURES + ENGINEERED_FEATURES

TARGET_CLASS: str = "placed"
TARGET_REG: str = "salary_lpa"


# ==========================================================
# D) FEATURE ENGINEERING CONSTANTS
# ==========================================================
EXPERIENCE_WEIGHTS: Dict[str, float] = {
    "internships": 2.0,
    "projects": 1.0,
    "certifications": 0.5,
}
MAX_EXPERIENCE_RAW: float = sum(
    EXPERIENCE_WEIGHTS[col] * float(FEATURE_RANGES[col][1]) for col in EXPERIENCE_COLS
)
BACKLOG_PENALTY: float = 0.5


# ==========================================================
# E) SAMPLE_STUDENT
# ==========================================================
SAMPLE_STUDENT: Dict[str, Union[int, float]] = {
    "cgpa": 8.4,
    "backlogs": 0,
    "attendance": 85,
    "internships": 1,
    "projects": 3,
    "certifications": 2,
    "dsa": 7,
    "programming": 8,
    "sql": 5,
    "cloud": 3,
    "web": 6,
    "communication": 6,
    "aptitude": 7,
}

# ==========================================================
# F) MODULE 2: MODELS CONFIGURATION
# --- Module 2: Models ---
# ==========================================================
CV_FOLDS: int = 5
MODEL_SELECTION_AUC_TOLERANCE: float = 0.005  # classifiers within this AUC of the best are tied; ties broken by lower Brier
CLASSIFICATION_THRESHOLD: float = 0.5
PERMUTATION_REPEATS: int = 10
MONOTONIC_CHECK_SAMPLES: int = 200

CLASSIFIER_PARAM_GRIDS: Dict[str, Dict[str, List[Any]]] = {
    "logistic_regression": {"model__C": [0.01, 0.1, 1.0, 10.0]},
    "decision_tree": {
        "model__max_depth": [3, 5, 7, 10],
        "model__min_samples_leaf": [5, 10, 20],
    },
    "random_forest": {
        "model__n_estimators": [200],
        "model__max_depth": [6, 10],
        "model__min_samples_leaf": [3, 5, 10],
    },
}

REGRESSOR_PARAM_GRIDS: Dict[str, Dict[str, List[Any]]] = {
    "linear_regression": {"model__fit_intercept": [True]},
    "random_forest_regressor": {
        "model__n_estimators": [200, 300],
        "model__max_depth": [6, 10, None],
        "model__min_samples_leaf": [2, 5, 10],
    },
}

# Readiness score (0-100). Weights must sum to 1.0.
READINESS_WEIGHTS: Dict[str, float] = {
    "probability": 0.50,
    "tech_score": 0.25,
    "soft_score": 0.15,
    "experience_score": 0.10,
}

# Risk level thresholds on placement probability (0-1)
RISK_LOW_THRESHOLD: float = 0.75  # probability >= 0.75 -> LOW
RISK_MEDIUM_THRESHOLD: float = 0.45  # 0.45 <= probability < 0.75 -> MEDIUM, else HIGH
RISK_LABELS: Tuple[str, ...] = ("LOW", "MEDIUM", "HIGH")

SALARY_RANGE_PCT: float = 0.15
SALARY_FLOOR_LPA: float = 3.0
SALARY_CAP_LPA: float = 30.0

FIGURE_FILES: Dict[str, str] = {
    "model_comparison_classifier": "model_comparison_classifier.png",
    "roc_curves": "roc_curves.png",
    "confusion_matrix": "confusion_matrix.png",
    "calibration_curve": "calibration_curve.png",
    "feature_importance_classifier": "feature_importance_classifier.png",
    "model_comparison_regressor": "model_comparison_regressor.png",
    "salary_actual_vs_predicted": "salary_actual_vs_predicted.png",
    "feature_importance_regressor": "feature_importance_regressor.png",
}

MONOTONIC_RAW_FEATURES: List[str] = [
    "dsa",
    "programming",
    "sql",
    "cloud",
    "web",
    "communication",
    "aptitude",
    "projects",
    "internships",
    "certifications",
]


# ==========================================================
# G) MODULE 3: SKILL GAP & RECOMMENDATION ENGINE
# --- Module 3: Skill Gap & Recommendations ---
# ==========================================================
SKILL_COLS: List[str] = TECH_SKILL_COLS + SOFT_SKILL_COLS  # canonical order, 7 skills
FEATURE_LABELS: Dict[str, str] = {
    "cgpa": "CGPA",
    "backlogs": "Backlogs",
    "attendance": "Attendance",
    "internships": "Internships",
    "projects": "Projects",
    "certifications": "Certifications",
    "dsa": "DSA",
    "programming": "Programming",
    "sql": "SQL",
    "cloud": "Cloud",
    "web": "Web Development",
    "communication": "Communication",
    "aptitude": "Aptitude",
}
DEFAULT_ROLE: str = "Software Developer"

STATUS_GOOD: str = "GOOD"
STATUS_MODERATE: str = "MODERATE"
STATUS_WEAK: str = "WEAK"
MODERATE_MAX_GAP: int = 2  # gap = benchmark - score
# gap <= 0 -> GOOD ; 0 < gap <= 2 -> MODERATE ; gap > 2 -> WEAK
SEVERITY_HIGH: str = "HIGH"
SEVERITY_MEDIUM: str = "MEDIUM"
SEVERITY_LOW: str = "LOW"
SEVERITY_ORDER: Dict[str, int] = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

ROLE_PROFILES: Dict[str, Dict[str, Any]] = {
    "Software Developer": {
        "description": "Builds and maintains software products and services.",
        "skill_benchmarks": {
            "dsa": 8,
            "programming": 8,
            "sql": 6,
            "cloud": 5,
            "web": 6,
            "communication": 6,
            "aptitude": 6,
        },
        "skill_importance": {
            "dsa": 3.0,
            "programming": 3.0,
            "sql": 2.0,
            "cloud": 1.5,
            "web": 2.0,
            "communication": 1.5,
            "aptitude": 1.5,
        },
        "profile_requirements": {
            "projects": 3,
            "internships": 1,
            "certifications": 1,
            "cgpa": 7.0,
            "attendance": 75,
        },
    },
    "Data Analyst": {
        "description": "Turns data into reports, dashboards and business insights.",
        "skill_benchmarks": {
            "dsa": 5,
            "programming": 6,
            "sql": 8,
            "cloud": 4,
            "web": 4,
            "communication": 8,
            "aptitude": 7,
        },
        "skill_importance": {
            "dsa": 1.0,
            "programming": 2.0,
            "sql": 3.0,
            "cloud": 1.0,
            "web": 1.0,
            "communication": 3.0,
            "aptitude": 2.5,
        },
        "profile_requirements": {
            "projects": 3,
            "internships": 1,
            "certifications": 2,
            "cgpa": 7.0,
            "attendance": 75,
        },
    },
    "Data Scientist": {
        "description": "Builds statistical and machine learning models on data.",
        "skill_benchmarks": {
            "dsa": 6,
            "programming": 8,
            "sql": 7,
            "cloud": 5,
            "web": 3,
            "communication": 7,
            "aptitude": 8,
        },
        "skill_importance": {
            "dsa": 2.0,
            "programming": 3.0,
            "sql": 2.5,
            "cloud": 1.5,
            "web": 1.0,
            "communication": 2.0,
            "aptitude": 3.0,
        },
        "profile_requirements": {
            "projects": 3,
            "internships": 1,
            "certifications": 2,
            "cgpa": 7.5,
            "attendance": 75,
        },
    },
}
PROFILE_MAX_BACKLOGS: int = 0  # global rule: no backlogs

PROFILE_RULE_WEIGHTS: Dict[str, float] = {
    "projects": 1.5,
    "internships": 2.0,
    "certifications": 0.5,
    "backlogs": 2.5,
    "cgpa": 1.0,
    "attendance": 0.3,
}
PROJECTS_HIGH_SHORTFALL: int = 2  # projects shortfall >= 2 -> HIGH, else MEDIUM
SKILL_SEVERITY: Dict[str, str] = {"WEAK": "HIGH", "MODERATE": "MEDIUM"}

SKILL_ACTIONS: Dict[str, Dict[str, str]] = {
    "dsa": {
        "WEAK": "Start DSA fundamentals (arrays, strings, hashing, recursion), then solve 3-4 easy problems a week on LeetCode or HackerRank.",
        "MODERATE": "Practice medium-level problems on trees, graphs and dynamic programming; aim for 100 solved problems and do timed mock rounds.",
    },
    "programming": {
        "WEAK": "Strengthen core programming in one language (Python, Java or C++): write small programs daily and finish a structured beginner-to-intermediate course.",
        "MODERATE": "Deepen your main language: OOP, error handling, clean code and basic testing; refactor one of your older projects.",
    },
    "sql": {
        "WEAK": "Learn SQL basics (SELECT, WHERE, GROUP BY, JOINs), then solve 30 beginner problems on HackerRank or LeetCode.",
        "MODERATE": "Practice 50 SQL problems on LeetCode or HackerRank covering joins, subqueries and window functions.",
    },
    "cloud": {
        "WEAK": "Learn cloud fundamentals (compute, storage, networking, IAM) through the free learning paths of AWS, Azure or GCP, and consider a foundational cloud certification.",
        "MODERATE": "Deploy one of your projects on a cloud platform and learn basic services (virtual machines, object storage, a managed database).",
    },
    "web": {
        "WEAK": "Learn HTML, CSS and JavaScript basics, then build a small responsive website.",
        "MODERATE": "Build a full-stack project with a framework (React, Flask, Django or Node) including REST APIs and deployment.",
    },
    "communication": {
        "WEAK": "Practice speaking daily: explain a technical topic aloud for 5 minutes, join a club or group discussions, and record yourself.",
        "MODERATE": "Do 3-4 mock HR and technical interviews with peers and practice structuring answers (situation, task, action, result).",
    },
    "aptitude": {
        "WEAK": "Start aptitude basics (percentages, ratios, time and work, logical reasoning) with about 20 questions a day.",
        "MODERATE": "Take timed aptitude mock tests weekly and review mistakes by topic (quant, logical, verbal).",
    },
}

PROFILE_ACTIONS: Dict[str, str] = {
    "projects": "Build {shortfall} more industry-level project(s) with a real use case, a GitHub repository and a short write-up.",
    "internships": "Apply for internships (on-campus, off-campus or remote) or contribute to open-source projects to gain real-world experience.",
    "certifications": "Earn {shortfall} relevant certification(s) (for example from Coursera, NPTEL, Google or Microsoft learning paths) aligned with your target role.",
    "backlogs": "Clear your {current} backlog(s) as early as possible; many companies require no active backlogs.",
    "cgpa": "Raise your CGPA toward {target}: focus on upcoming semester scores, since many companies apply a CGPA cutoff.",
    "attendance": "Improve attendance to at least {target}% to avoid eligibility issues.",
}
MAINTAIN_MESSAGE: str = "Your profile meets the benchmark for this role. Keep practicing with mock interviews and stay updated on current tools."

# --- Module 4 will append sections below ---

