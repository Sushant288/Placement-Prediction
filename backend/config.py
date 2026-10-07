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

# --- Modules 3-4 will append sections below ---

