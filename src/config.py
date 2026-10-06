"""Configuration settings: benchmarks, role requirements, thresholds, and project paths."""

from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_PATH = DATA_DIR / "raw" / "placement_data.csv"
PROCESSED_DATA_PATH = DATA_DIR / "processed" / "clean_data.csv"

MODELS_DIR = BASE_DIR / "models"
PLACEMENT_MODEL_PATH = MODELS_DIR / "placement_model.pkl"
SALARY_MODEL_PATH = MODELS_DIR / "salary_model.pkl"
METRICS_PATH = MODELS_DIR / "metrics.json"

REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# Benchmarks & Thresholds
DEFAULT_RANDOM_STATE = 42
PLACEMENT_PROBABILITY_THRESHOLD = 0.5

# Target Job Role Benchmarks and Requirements
ROLE_REQUIREMENTS = {
    "Software Engineer": {
        "min_cgpa": 7.0,
        "min_internships": 1,
        "min_projects": 2,
        "min_coding_score": 75,
        "min_communication_score": 60,
    },
    "Data Scientist": {
        "min_cgpa": 7.5,
        "min_internships": 1,
        "min_projects": 3,
        "min_coding_score": 70,
        "min_communication_score": 65,
    },
    "Data Analyst": {
        "min_cgpa": 6.5,
        "min_internships": 0,
        "min_projects": 2,
        "min_coding_score": 60,
        "min_communication_score": 70,
    },
}
