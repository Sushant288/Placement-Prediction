"""Module 2: Inference and Prediction API.

Provides cached model inference, risk classification, readiness scoring,
salary range estimation, and model performance metrics inspection.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

import backend.config as cfg
from backend.config import (
    ENGINEERED_FEATURES,
    METRICS_PATH,
    MODEL_FEATURES,
    PLACEMENT_MODEL_PATH,
    READINESS_WEIGHTS,
    RISK_LOW_THRESHOLD,
    RISK_MEDIUM_THRESHOLD,
    SALARY_CAP_LPA,
    SALARY_FLOOR_LPA,
    SALARY_MODEL_PATH,
    SALARY_RANGE_PCT,
    SAMPLE_STUDENT,
)
from backend.preprocessing import preprocess_input

# Module-level cache for lazy loading
_CLASSIFIER: Optional[Pipeline] = None
_REGRESSOR: Optional[Pipeline] = None
_METRICS: Optional[Dict[str, Any]] = None


def reload_models() -> None:
    """Clear cached models and metrics to force reload on subsequent inference calls."""
    global _CLASSIFIER, _REGRESSOR, _METRICS
    _CLASSIFIER = None
    _REGRESSOR = None
    _METRICS = None


def _get_active_classifier_path() -> Path:
    """Resolve active placement model path allowing for runtime configuration monkeypatching."""
    if (
        hasattr(cfg, "PLACEMENT_MODEL_PATH")
        and Path(cfg.PLACEMENT_MODEL_PATH) != Path(PLACEMENT_MODEL_PATH)
    ):
        return Path(cfg.PLACEMENT_MODEL_PATH)
    return Path(PLACEMENT_MODEL_PATH)


def _get_active_salary_path() -> Path:
    """Resolve active salary model path allowing for runtime configuration monkeypatching."""
    if (
        hasattr(cfg, "SALARY_MODEL_PATH")
        and Path(cfg.SALARY_MODEL_PATH) != Path(SALARY_MODEL_PATH)
    ):
        return Path(cfg.SALARY_MODEL_PATH)
    return Path(SALARY_MODEL_PATH)


def _get_active_metrics_path() -> Path:
    """Resolve active metrics path allowing for runtime configuration monkeypatching."""
    if (
        hasattr(cfg, "METRICS_PATH")
        and Path(cfg.METRICS_PATH) != Path(METRICS_PATH)
    ):
        return Path(cfg.METRICS_PATH)
    return Path(METRICS_PATH)


def _get_classifier() -> Pipeline:
    """Retrieve or lazily load the serialized placement classification pipeline."""
    global _CLASSIFIER
    clf_path = _get_active_classifier_path()
    if not clf_path.exists():
        raise FileNotFoundError(
            "Model files not found. Run: python -m backend.train_models"
        )
    if _CLASSIFIER is None:
        _CLASSIFIER = joblib.load(clf_path)
    return _CLASSIFIER


def _get_regressor() -> Pipeline:
    """Retrieve or lazily load the serialized salary regression pipeline."""
    global _REGRESSOR
    reg_path = _get_active_salary_path()
    if not reg_path.exists():
        raise FileNotFoundError(
            "Model files not found. Run: python -m backend.train_models"
        )
    if _REGRESSOR is None:
        _REGRESSOR = joblib.load(reg_path)
    return _REGRESSOR


def get_risk_level(probability: float) -> str:
    """Determine risk category based on placement probability."""
    if probability >= RISK_LOW_THRESHOLD:
        return "LOW"
    elif probability >= RISK_MEDIUM_THRESHOLD:
        return "MEDIUM"
    else:
        return "HIGH"


def compute_readiness_score(
    probability: float, engineered: Dict[str, float]
) -> float:
    """Calculate overall student readiness score on a 0-100 scale."""
    w = READINESS_WEIGHTS
    score = 100.0 * (
        w["probability"] * probability
        + w["tech_score"] * (engineered["tech_score"] / 10.0)
        + w["soft_score"] * (engineered["soft_score"] / 10.0)
        + w["experience_score"] * (engineered["experience_score"] / 10.0)
    )
    score_clipped = max(0.0, min(100.0, float(score)))
    return round(score_clipped, 1)


def make_salary_range(salary: float) -> Dict[str, object]:
    """Compute bounded upper and lower package expectations around point estimate."""
    low = salary * (1.0 - SALARY_RANGE_PCT)
    high = salary * (1.0 + SALARY_RANGE_PCT)
    low = max(SALARY_FLOOR_LPA, min(SALARY_CAP_LPA, low))
    high = max(SALARY_FLOOR_LPA, min(SALARY_CAP_LPA, high))
    low_r = round(float(low), 1)
    high_r = round(float(high), 1)

    if low_r == high_r:
        if high_r + 0.1 <= SALARY_CAP_LPA:
            high_r = round(high_r + 0.1, 1)
        elif low_r - 0.1 >= SALARY_FLOOR_LPA:
            low_r = round(low_r - 0.1, 1)

    label = f"{low_r:.1f} - {high_r:.1f} LPA"
    return {"low": low_r, "high": high_r, "label": label}


def predict_probability(student: Dict[str, float]) -> float:
    """Compute placement probability (0-1) for a single candidate."""
    clf = _get_classifier()
    df_single = preprocess_input(student)
    prob = float(clf.predict_proba(df_single)[0, 1])
    return prob


def predict_student(student: Dict[str, float]) -> Dict[str, object]:
    """Execute full prediction pipeline for a student candidate."""
    clf = _get_classifier()
    reg = _get_regressor()

    # Preprocess and validate inputs (propagates ValueError on invalid keys or types)
    df_single = preprocess_input(student)

    # 1. Placement classification probability
    prob = float(clf.predict_proba(df_single)[0, 1])
    prob_rounded = round(prob, 4)
    prob_pct = round(prob * 100.0, 1)

    # 2. Conditional salary regression (package IF placed)
    raw_salary = float(reg.predict(df_single)[0])
    salary_estimate = round(
        max(SALARY_FLOOR_LPA, min(SALARY_CAP_LPA, raw_salary)), 1
    )
    salary_range = make_salary_range(salary_estimate)

    # 3. Extract engineered feature scores
    engineered_scores: Dict[str, float] = {
        k: float(df_single[k].iloc[0]) for k in ENGINEERED_FEATURES
    }

    # 4. Readiness score & Risk level
    readiness = compute_readiness_score(prob, engineered_scores)
    risk = get_risk_level(prob)

    return {
        "probability": prob_rounded,
        "probability_pct": prob_pct,
        "salary_estimate": salary_estimate,
        "salary_range": salary_range,
        "readiness_score": readiness,
        "risk_level": risk,
        "engineered_scores": engineered_scores,
    }


def get_model_metrics() -> Dict[str, Any]:
    """Load and return serialized training and evaluation metrics from disk."""
    global _METRICS
    metrics_path = _get_active_metrics_path()
    if not metrics_path.exists():
        raise FileNotFoundError(
            "Model files not found. Run: python -m backend.train_models"
        )
    if _METRICS is None:
        with open(metrics_path, "r", encoding="utf-8") as f:
            _METRICS = json.load(f)
    return _METRICS


def get_feature_importance(
    model: str = "classifier", top_n: int = 12
) -> Dict[str, float]:
    """Retrieve top permutation feature importances sorted descending for specified model."""
    if model not in ("classifier", "regressor"):
        raise ValueError(
            f"Invalid model '{model}'. Must be 'classifier' or 'regressor'."
        )
    metrics = get_model_metrics()
    feat_data = metrics[model]["feature_importance"]
    sorted_feats = sorted(
        feat_data.items(), key=lambda item: item[1]["mean"], reverse=True
    )
    return {k: v["mean"] for k, v in sorted_feats[:top_n]}


if __name__ == "__main__":
    report = predict_student(SAMPLE_STUDENT)
    print("==============================")
    print(" PLACEMENT ANALYSIS")
    print("==============================")
    print(f"Placement Probability : {report['probability_pct']}%")
    print(f"Readiness Score       : {report['readiness_score']} / 100")
    print(f"Expected Package      : {report['salary_range']['label']} (if placed)")
    print(f"Risk Level            : {report['risk_level']}")
