"""Module 2: Model Training, Evaluation, and Serialization.

Trains and tunes classification models for placement prediction and
regression models for conditional salary estimation using scikit-learn Pipelines.
Strictly adheres to data leakage guards: train.csv for fitting/selection, test.csv for evaluation.
"""

import datetime
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.calibration import calibration_curve
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
    roc_curve,
    root_mean_squared_error,
)
from sklearn.model_selection import GridSearchCV, KFold, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
import sklearn
import joblib

from backend.config import (
    CLASSIFICATION_THRESHOLD,
    CLASSIFIER_PARAM_GRIDS,
    CV_FOLDS,
    FEATURE_RANGES,
    FIGURE_FILES,
    FIGURES_DIR,
    METRICS_PATH,
    MODEL_FEATURES,
    MODEL_SELECTION_AUC_TOLERANCE,
    MODELS_DIR,
    MONOTONIC_CHECK_SAMPLES,
    MONOTONIC_RAW_FEATURES,
    PERMUTATION_REPEATS,
    PLACEMENT_MODEL_PATH,
    RANDOM_SEED,
    RAW_FEATURES,
    REGRESSOR_PARAM_GRIDS,
    SALARY_MODEL_PATH,
    TARGET_CLASS,
    TARGET_REG,
)
from backend.preprocessing import load_train_test, preprocess_input


def _run_monotonic_diagnostic(
    fitted_models: Dict[str, Pipeline],
    test_df: pd.DataFrame,
) -> Dict[str, float]:
    """Calculate monotonicity violation rate for each candidate classifier on test samples."""
    n_samples = min(MONOTONIC_CHECK_SAMPLES, len(test_df))
    sample_df = test_df.sample(n=n_samples, random_state=RANDOM_SEED)
    sample_dicts = sample_df[RAW_FEATURES].to_dict(orient="records")

    # Generate baseline preprocessed inputs
    base_dfs = [preprocess_input(s) for s in sample_dicts]
    base_df_all = pd.concat(base_dfs, ignore_index=True)

    # Generate perturbed inputs
    pert_records: List[Tuple[int, pd.DataFrame]] = []
    for s_idx, student in enumerate(sample_dicts):
        for feat in MONOTONIC_RAW_FEATURES:
            cur_val = student[feat]
            max_val = FEATURE_RANGES[feat][1]
            pert_student = dict(student)
            pert_student[feat] = min(cur_val + 1, max_val)
            pert_records.append((s_idx, preprocess_input(pert_student)))

    pert_df_all = pd.concat([pr[1] for pr in pert_records], ignore_index=True)
    pert_indices = np.array([pr[0] for pr in pert_records])

    violation_rates: Dict[str, float] = {}
    total_checks = len(pert_df_all)

    for name, model in fitted_models.items():
        base_probs = model.predict_proba(base_df_all)[:, 1]
        pert_probs = model.predict_proba(pert_df_all)[:, 1]
        base_matched = base_probs[pert_indices]
        drops = base_matched - pert_probs
        # Count violations where probability drops by strictly more than 0.02
        violations = int((drops > 0.02).sum())
        rate = float(violations / total_checks) if total_checks > 0 else 0.0
        violation_rates[name] = round(rate, 4)

    return violation_rates


def _generate_classifier_figures(
    fitted_models: Dict[str, Pipeline],
    selected_name: str,
    classifier_dict: Dict[str, Any],
    test_df: pd.DataFrame,
) -> None:
    """Generate figures 1 through 5 for placement classification."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    X_test = test_df[MODEL_FEATURES]
    y_test = test_df[TARGET_CLASS]

    # 1. model_comparison_classifier.png
    plt.figure(figsize=(10, 6))
    clf_records = []
    for model_name, info in classifier_dict["models"].items():
        t = info["test"]
        for metric in ["accuracy", "precision", "recall", "f1", "roc_auc"]:
            clf_records.append({
                "Model": model_name,
                "Metric": metric.replace("_", " ").title(),
                "Score": t[metric],
            })
    clf_comp_df = pd.DataFrame(clf_records)
    ax = sns.barplot(
        data=clf_comp_df, x="Metric", y="Score", hue="Model", palette="deep"
    )
    plt.title("Classifier Performance Comparison (Test Set)", fontsize=14, pad=12)
    plt.ylim(0.0, 1.05)
    plt.xlabel("Evaluation Metric", fontsize=11)
    plt.ylabel("Score", fontsize=11)
    plt.legend(title="Model", frameon=True)
    for p in ax.patches:
        height = p.get_height()
        if not np.isnan(height) and height > 0:
            ax.annotate(
                f"{height:.2f}",
                (p.get_x() + p.get_width() / 2.0, height),
                ha="center",
                va="bottom",
                fontsize=8,
                xytext=(0, 2),
                textcoords="offset points",
            )
    plt.savefig(
        FIGURES_DIR / FIGURE_FILES["model_comparison_classifier"],
        dpi=150,
        bbox_inches="tight",
    )
    plt.close()

    # 2. roc_curves.png
    plt.figure(figsize=(8, 6))
    for model_name, model in fitted_models.items():
        y_proba = model.predict_proba(X_test)[:, 1]
        fpr, tpr, _ = roc_curve(y_test, y_proba)
        auc_score = classifier_dict["models"][model_name]["test"]["roc_auc"]
        plt.plot(fpr, tpr, lw=2, label=f"{model_name} (AUC = {auc_score:.3f})")
    plt.plot([0, 1], [0, 1], "k--", lw=1.5, label="Random Chance (AUC = 0.50)")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("False Positive Rate", fontsize=11)
    plt.ylabel("True Positive Rate", fontsize=11)
    plt.title("ROC Curves Comparison (Test Set)", fontsize=14, pad=12)
    plt.legend(loc="lower right", frameon=True)
    plt.savefig(
        FIGURES_DIR / FIGURE_FILES["roc_curves"],
        dpi=150,
        bbox_inches="tight",
    )
    plt.close()

    # 3. confusion_matrix.png
    plt.figure(figsize=(6, 5))
    cm = np.array(
        classifier_dict["models"][selected_name]["test"]["confusion_matrix"]
    )
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        cbar=False,
        xticklabels=["Not Placed", "Placed"],
        yticklabels=["Not Placed", "Placed"],
    )
    plt.title(f"Confusion Matrix: {selected_name} (Test Set)", fontsize=14, pad=12)
    plt.xlabel("Predicted Class", fontsize=11)
    plt.ylabel("Actual Class", fontsize=11)
    plt.savefig(
        FIGURES_DIR / FIGURE_FILES["confusion_matrix"],
        dpi=150,
        bbox_inches="tight",
    )
    plt.close()

    # 4. calibration_curve.png
    plt.figure(figsize=(7, 6))
    best_clf = fitted_models[selected_name]
    y_prob_best = best_clf.predict_proba(X_test)[:, 1]
    prob_true, prob_pred = calibration_curve(
        y_test, y_prob_best, n_bins=10
    )
    plt.plot(
        prob_pred,
        prob_true,
        marker="o",
        lw=2,
        color="teal",
        label=f"{selected_name}",
    )
    plt.plot([0, 1], [0, 1], "k--", lw=1.5, label="Perfectly Calibrated")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.0])
    plt.xlabel("Mean Predicted Probability", fontsize=11)
    plt.ylabel("Fraction of Positives", fontsize=11)
    plt.title(
        f"Reliability Diagram (Calibration): {selected_name}",
        fontsize=14,
        pad=12,
    )
    plt.legend(loc="upper left", frameon=True)
    plt.savefig(
        FIGURES_DIR / FIGURE_FILES["calibration_curve"],
        dpi=150,
        bbox_inches="tight",
    )
    plt.close()

    # 5. feature_importance_classifier.png
    plt.figure(figsize=(9, 6))
    top_items = list(classifier_dict["feature_importance"].items())[:12]
    feats = [item[0] for item in top_items]
    means = [item[1]["mean"] for item in top_items]
    stds = [item[1]["std"] for item in top_items]

    y_pos = np.arange(len(feats))
    plt.barh(
        y_pos,
        means[::-1],
        xerr=stds[::-1],
        align="center",
        color="steelblue",
        alpha=0.85,
        capsize=3,
    )
    plt.yticks(y_pos, feats[::-1], fontsize=10)
    plt.xlabel("Permutation Importance (Mean ROC-AUC Drop)", fontsize=11)
    plt.ylabel("Feature", fontsize=11)
    plt.title(
        f"Top 12 Classifier Features: {selected_name} (Test Set)",
        fontsize=14,
        pad=12,
    )
    plt.savefig(
        FIGURES_DIR / FIGURE_FILES["feature_importance_classifier"],
        dpi=150,
        bbox_inches="tight",
    )
    plt.close()


def _generate_regressor_figures(
    fitted_regressors: Dict[str, Pipeline],
    selected_name: str,
    regressor_dict: Dict[str, Any],
    test_df: pd.DataFrame,
) -> None:
    """Generate figures 6 through 8 for conditional salary regression."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    test_placed = test_df[test_df[TARGET_CLASS] == 1].copy()
    X_test_placed = test_placed[MODEL_FEATURES]
    y_test_placed = test_placed[TARGET_REG]

    # 6. model_comparison_regressor.png
    plt.figure(figsize=(8, 5))
    reg_records = []
    for model_name, info in regressor_dict["models"].items():
        t = info["test"]
        reg_records.append({
            "Model": model_name,
            "Metric": "MAE",
            "Error (LPA)": t["mae"],
        })
        reg_records.append({
            "Model": model_name,
            "Metric": "RMSE",
            "Error (LPA)": t["rmse"],
        })
    reg_comp_df = pd.DataFrame(reg_records)
    ax = sns.barplot(
        data=reg_comp_df,
        x="Metric",
        y="Error (LPA)",
        hue="Model",
        palette="muted",
    )
    plt.title("Salary Regressor Error Comparison (Placed Test Set)", fontsize=14, pad=12)
    plt.xlabel("Metric", fontsize=11)
    plt.ylabel("Error in LPA", fontsize=11)
    plt.legend(title="Model", frameon=True)
    for p in ax.patches:
        height = p.get_height()
        if not np.isnan(height) and height > 0:
            ax.annotate(
                f"{height:.2f}",
                (p.get_x() + p.get_width() / 2.0, height),
                ha="center",
                va="bottom",
                fontsize=8,
                xytext=(0, 2),
                textcoords="offset points",
            )
    plt.savefig(
        FIGURES_DIR / FIGURE_FILES["model_comparison_regressor"],
        dpi=150,
        bbox_inches="tight",
    )
    plt.close()

    # 7. salary_actual_vs_predicted.png
    plt.figure(figsize=(7, 6))
    best_reg = fitted_regressors[selected_name]
    y_pred_reg = best_reg.predict(X_test_placed)
    r2_val = regressor_dict["models"][selected_name]["test"]["r2"]

    plt.scatter(
        y_test_placed,
        y_pred_reg,
        alpha=0.6,
        color="indigo",
        edgecolors="none",
        label="Placed Students",
    )
    min_val = min(float(y_test_placed.min()), float(y_pred_reg.min()))
    max_val = max(float(y_test_placed.max()), float(y_pred_reg.max()))
    plt.plot(
        [min_val, max_val],
        [min_val, max_val],
        "r--",
        lw=2,
        label="Ideal Fit (y = x)",
    )
    plt.title(
        f"Actual vs Predicted Salary (R2 = {r2_val:.3f})",
        fontsize=14,
        pad=12,
    )
    plt.xlabel("Actual Salary (LPA)", fontsize=11)
    plt.ylabel("Predicted Salary (LPA)", fontsize=11)
    plt.legend(loc="upper left", frameon=True)
    plt.savefig(
        FIGURES_DIR / FIGURE_FILES["salary_actual_vs_predicted"],
        dpi=150,
        bbox_inches="tight",
    )
    plt.close()

    # 8. feature_importance_regressor.png
    plt.figure(figsize=(9, 6))
    top_items_reg = list(regressor_dict["feature_importance"].items())[:12]
    feats_reg = [item[0] for item in top_items_reg]
    means_reg = [item[1]["mean"] for item in top_items_reg]
    stds_reg = [item[1]["std"] for item in top_items_reg]

    y_pos = np.arange(len(feats_reg))
    plt.barh(
        y_pos,
        means_reg[::-1],
        xerr=stds_reg[::-1],
        align="center",
        color="darkolivegreen",
        alpha=0.85,
        capsize=3,
    )
    plt.yticks(y_pos, feats_reg[::-1], fontsize=10)
    plt.xlabel("Permutation Importance (Mean R2 Drop)", fontsize=11)
    plt.ylabel("Feature", fontsize=11)
    plt.title(
        f"Top 12 Regressor Features: {selected_name} (Placed Test Set)",
        fontsize=14,
        pad=12,
    )
    plt.savefig(
        FIGURES_DIR / FIGURE_FILES["feature_importance_regressor"],
        dpi=150,
        bbox_inches="tight",
    )
    plt.close()


def train_classifiers(
    train_df: pd.DataFrame, test_df: pd.DataFrame
) -> Tuple[Pipeline, Dict[str, Any]]:
    """Train, cross-validate, select, and evaluate placement classification models.

    LEAKAGE RULE: Model fitting and selection rely strictly on train_df.
    test_df is evaluated only after selection is finalized.
    """
    X_train = train_df[MODEL_FEATURES]
    y_train = train_df[TARGET_CLASS]

    candidate_pipelines: Dict[str, Pipeline] = {
        "logistic_regression": Pipeline([
            ("scaler", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    max_iter=2000, random_state=RANDOM_SEED
                ),
            ),
        ]),
        "decision_tree": Pipeline([
            ("model", DecisionTreeClassifier(random_state=RANDOM_SEED)),
        ]),
        "random_forest": Pipeline([
            (
                "model",
                RandomForestClassifier(
                    random_state=RANDOM_SEED, n_jobs=-1
                ),
            ),
        ]),
    }

    cv = StratifiedKFold(
        n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_SEED
    )
    fitted_models: Dict[str, Pipeline] = {}
    cv_records: Dict[str, Dict[str, Any]] = {}

    print("Fitting candidate classifiers with Stratified 5-Fold CV on train data...")
    for name, pipe in candidate_pipelines.items():
        grid = GridSearchCV(
            estimator=pipe,
            param_grid=CLASSIFIER_PARAM_GRIDS[name],
            cv=cv,
            scoring={"roc_auc": "roc_auc", "neg_brier": "neg_brier_score"},
            refit="roc_auc",
            n_jobs=-1,
        )
        grid.fit(X_train, y_train)
        best_idx = grid.best_index_
        best_cv_auc = float(grid.cv_results_["mean_test_roc_auc"][best_idx])
        best_cv_brier = float(-grid.cv_results_["mean_test_neg_brier"][best_idx])

        fitted_models[name] = grid.best_estimator_
        cv_records[name] = {
            "best_params": grid.best_params_,
            "cv_roc_auc": round(best_cv_auc, 4),
            "cv_brier": round(best_cv_brier, 4),
        }
        print(
            f"  - {name:20s} | CV ROC-AUC: {best_cv_auc:.4f} | CV Brier: {best_cv_brier:.4f}"
        )

    # Model Selection (purely CV based on train data)
    best_cv_auc = max(rec["cv_roc_auc"] for rec in cv_records.values())
    tolerance_threshold = best_cv_auc - MODEL_SELECTION_AUC_TOLERANCE
    candidates = [
        name
        for name, rec in cv_records.items()
        if rec["cv_roc_auc"] >= tolerance_threshold
    ]
    # Tie breaking by lowest CV Brier
    selected_name = min(candidates, key=lambda n: cv_records[n]["cv_brier"])
    best_classifier = fitted_models[selected_name]

    if len(candidates) > 1:
        selection_reason = (
            f"Candidate '{selected_name}' selected: within {MODEL_SELECTION_AUC_TOLERANCE} "
            f"AUC tolerance of best CV ROC-AUC ({best_cv_auc:.4f}), broken by lowest CV Brier "
            f"({cv_records[selected_name]['cv_brier']:.4f})."
        )
    else:
        selection_reason = (
            f"Candidate '{selected_name}' selected with highest CV ROC-AUC ({best_cv_auc:.4f}) "
            f"and lowest CV Brier ({cv_records[selected_name]['cv_brier']:.4f})."
        )
    print(f"Classifier selected: {selected_name}")
    print(f"Selection reason: {selection_reason}")

    # Test evaluation (run on test_df for reporting)
    X_test = test_df[MODEL_FEATURES]
    y_test = test_df[TARGET_CLASS]
    train_placement_rate = float(y_train.mean())
    baseline_brier = float(
        brier_score_loss(
            y_test, np.full_like(y_test, train_placement_rate, dtype=float)
        )
    )

    # Monotonicity diagnostic
    monotonic_rates = _run_monotonic_diagnostic(fitted_models, test_df)
    if monotonic_rates[selected_name] > 0.05:
        print(
            f"WARNING: Selected classifier monotonic violation rate ({monotonic_rates[selected_name]:.4f}) exceeds 0.05!"
        )

    models_metrics: Dict[str, Dict[str, Any]] = {}
    for name, model in fitted_models.items():
        y_proba = model.predict_proba(X_test)[:, 1]
        y_pred = (y_proba >= CLASSIFICATION_THRESHOLD).astype(int)
        cm = confusion_matrix(y_test, y_pred).tolist()

        models_metrics[name] = {
            "best_params": cv_records[name]["best_params"],
            "cv_roc_auc": cv_records[name]["cv_roc_auc"],
            "cv_brier": cv_records[name]["cv_brier"],
            "test": {
                "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
                "precision": round(
                    float(precision_score(y_test, y_pred, zero_division=0)), 4
                ),
                "recall": round(
                    float(recall_score(y_test, y_pred, zero_division=0)), 4
                ),
                "f1": round(
                    float(f1_score(y_test, y_pred, zero_division=0)), 4
                ),
                "roc_auc": round(float(roc_auc_score(y_test, y_proba)), 4),
                "brier_score": round(
                    float(brier_score_loss(y_test, y_proba)), 4
                ),
                "confusion_matrix": cm,
            },
            "monotonic_violation_rate": monotonic_rates[name],
        }

    # Permutation Importance for selected classifier on test_df
    print("Computing permutation feature importance for selected classifier on test data...")
    perm_res = permutation_importance(
        best_classifier,
        X_test,
        y_test,
        scoring="roc_auc",
        n_repeats=PERMUTATION_REPEATS,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    sorted_idx = np.argsort(perm_res.importances_mean)[::-1]
    feature_importance: Dict[str, Dict[str, float]] = {}
    for idx in sorted_idx:
        feat = MODEL_FEATURES[idx]
        feature_importance[feat] = {
            "mean": round(float(perm_res.importances_mean[idx]), 5),
            "std": round(float(perm_res.importances_std[idx]), 5),
        }

    classifier_dict: Dict[str, Any] = {
        "best_model": selected_name,
        "selection_reason": selection_reason,
        "models": models_metrics,
        "baseline_brier": round(baseline_brier, 4),
        "feature_importance": feature_importance,
    }

    _generate_classifier_figures(
        fitted_models, selected_name, classifier_dict, test_df
    )

    return best_classifier, classifier_dict


def train_regressors(
    train_df: pd.DataFrame, test_df: pd.DataFrame
) -> Tuple[Pipeline, Dict[str, Any]]:
    """Train, cross-validate, select, and evaluate conditional salary regressors.

    LEAKAGE RULE: Model fitting and selection rely strictly on train rows with placed == 1.
    Evaluation is conducted on test rows with placed == 1.
    """
    train_placed = train_df[train_df[TARGET_CLASS] == 1].copy()
    test_placed = test_df[test_df[TARGET_CLASS] == 1].copy()

    X_train_reg = train_placed[MODEL_FEATURES]
    y_train_reg = train_placed[TARGET_REG]
    X_test_reg = test_placed[MODEL_FEATURES]
    y_test_reg = test_placed[TARGET_REG]

    candidate_pipelines: Dict[str, Pipeline] = {
        "linear_regression": Pipeline([
            ("scaler", StandardScaler()),
            ("model", LinearRegression()),
        ]),
        "random_forest_regressor": Pipeline([
            (
                "model",
                RandomForestRegressor(
                    random_state=RANDOM_SEED, n_jobs=-1
                ),
            ),
        ]),
    }

    cv = KFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_SEED)
    fitted_regressors: Dict[str, Pipeline] = {}
    cv_records: Dict[str, Dict[str, Any]] = {}

    print("Fitting candidate regressors with 5-Fold CV on placed train data...")
    for name, pipe in candidate_pipelines.items():
        grid = GridSearchCV(
            estimator=pipe,
            param_grid=REGRESSOR_PARAM_GRIDS[name],
            cv=cv,
            scoring={
                "rmse": "neg_root_mean_squared_error",
                "mae": "neg_mean_absolute_error",
            },
            refit="rmse",
            n_jobs=-1,
        )
        grid.fit(X_train_reg, y_train_reg)
        best_idx = grid.best_index_
        best_cv_rmse = float(-grid.cv_results_["mean_test_rmse"][best_idx])
        best_cv_mae = float(-grid.cv_results_["mean_test_mae"][best_idx])

        fitted_regressors[name] = grid.best_estimator_
        cv_records[name] = {
            "best_params": grid.best_params_,
            "cv_rmse": round(best_cv_rmse, 4),
            "cv_mae": round(best_cv_mae, 4),
        }
        print(
            f"  - {name:25s} | CV RMSE: {best_cv_rmse:.4f} | CV MAE: {best_cv_mae:.4f}"
        )

    # Regressor selection: lowest CV RMSE
    selected_name = min(cv_records, key=lambda n: cv_records[n]["cv_rmse"])
    best_regressor = fitted_regressors[selected_name]
    selection_reason = (
        f"Candidate '{selected_name}' selected with lowest CV RMSE "
        f"({cv_records[selected_name]['cv_rmse']:.4f}) and CV MAE ({cv_records[selected_name]['cv_mae']:.4f})."
    )
    print(f"Regressor selected: {selected_name}")
    print(f"Selection reason: {selection_reason}")

    # Baseline RMSE on test placed rows
    train_mean_salary = float(y_train_reg.mean())
    baseline_rmse = float(
        root_mean_squared_error(
            y_test_reg, np.full_like(y_test_reg, train_mean_salary)
        )
    )

    models_metrics: Dict[str, Dict[str, Any]] = {}
    for name, model in fitted_regressors.items():
        y_pred = model.predict(X_test_reg)
        models_metrics[name] = {
            "best_params": cv_records[name]["best_params"],
            "cv_rmse": cv_records[name]["cv_rmse"],
            "cv_mae": cv_records[name]["cv_mae"],
            "test": {
                "mae": round(float(mean_absolute_error(y_test_reg, y_pred)), 4),
                "rmse": round(
                    float(root_mean_squared_error(y_test_reg, y_pred)), 4
                ),
                "r2": round(float(r2_score(y_test_reg, y_pred)), 4),
            },
        }

    # Permutation importance for selected regressor
    print("Computing permutation feature importance for selected regressor on test data...")
    perm_res = permutation_importance(
        best_regressor,
        X_test_reg,
        y_test_reg,
        scoring="r2",
        n_repeats=PERMUTATION_REPEATS,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    sorted_idx = np.argsort(perm_res.importances_mean)[::-1]
    feature_importance: Dict[str, Dict[str, float]] = {}
    for idx in sorted_idx:
        feat = MODEL_FEATURES[idx]
        feature_importance[feat] = {
            "mean": round(float(perm_res.importances_mean[idx]), 5),
            "std": round(float(perm_res.importances_std[idx]), 5),
        }

    regressor_dict: Dict[str, Any] = {
        "best_model": selected_name,
        "selection_reason": selection_reason,
        "models": models_metrics,
        "baseline_rmse": round(baseline_rmse, 4),
        "n_train_rows": int(len(train_placed)),
        "n_test_rows": int(len(test_placed)),
        "feature_importance": feature_importance,
    }

    _generate_regressor_figures(
        fitted_regressors, selected_name, regressor_dict, test_df
    )

    return best_regressor, regressor_dict


def main() -> None:
    """Execute model training, evaluation, comparison, figure generation, and artifact serialization."""
    start_time = time.time()
    print("=" * 60)
    print(" MODULE 2: MODEL TRAINING & EVALUATION PIPELINE")
    print("=" * 60)

    # Load train and test data
    train_df, test_df = load_train_test()
    print(f"Loaded train set ({len(train_df)} rows) and test set ({len(test_df)} rows).")

    # Train and evaluate models
    best_classifier, classifier_dict = train_classifiers(train_df, test_df)
    best_regressor, regressor_dict = train_regressors(train_df, test_df)

    # Save models
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_classifier, PLACEMENT_MODEL_PATH)
    joblib.dump(best_regressor, SALARY_MODEL_PATH)
    print(f"Saved placement classifier to: {PLACEMENT_MODEL_PATH}")
    print(f"Saved salary regressor to: {SALARY_MODEL_PATH}")

    # Build and write metrics.json
    placement_rate_train = float(train_df[TARGET_CLASS].mean())
    placement_rate_test = float(test_df[TARGET_CLASS].mean())

    metrics_payload: Dict[str, Any] = {
        "meta": {
            "trained_at": datetime.datetime.now().isoformat(),
            "seed": RANDOM_SEED,
            "sklearn_version": sklearn.__version__,
            "n_train": int(len(train_df)),
            "n_test": int(len(test_df)),
            "features": MODEL_FEATURES,
            "placement_rate_train": round(placement_rate_train, 4),
            "placement_rate_test": round(placement_rate_test, 4),
        },
        "classifier": classifier_dict,
        "regressor": regressor_dict,
    }

    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)
    print(f"Saved evaluation metrics to: {METRICS_PATH}")

    # Print summary tables (ASCII only)
    print("\n" + "=" * 78)
    print(" CLASSIFIER COMPARISON TABLE")
    print("=" * 78)
    print(
        f"{'Model':<22} | {'CV AUC':<8} | {'CV Brier':<8} | {'Test Acc':<8} | {'Test AUC':<8} | {'Test F1':<8} | {'Test Brier':<10}"
    )
    print("-" * 78)
    for name, info in classifier_dict["models"].items():
        t = info["test"]
        print(
            f"{name:<22} | {info['cv_roc_auc']:<8.4f} | {info['cv_brier']:<8.4f} | "
            f"{t['accuracy']:<8.4f} | {t['roc_auc']:<8.4f} | {t['f1']:<8.4f} | {t['brier_score']:<10.4f}"
        )
    print("-" * 78)
    print(f"Selected: {classifier_dict['best_model']}")
    print(f"Reason  : {classifier_dict['selection_reason']}")
    print(f"Baseline Brier (Test): {classifier_dict['baseline_brier']:.4f}")

    print("\n" + "=" * 78)
    print(" REGRESSOR COMPARISON TABLE (Placed Students)")
    print("=" * 78)
    print(
        f"{'Model':<25} | {'CV RMSE':<9} | {'CV MAE':<9} | {'Test RMSE':<9} | {'Test MAE':<9} | {'Test R2':<8}"
    )
    print("-" * 78)
    for name, info in regressor_dict["models"].items():
        t = info["test"]
        print(
            f"{name:<25} | {info['cv_rmse']:<9.4f} | {info['cv_mae']:<9.4f} | "
            f"{t['rmse']:<9.4f} | {t['mae']:<9.4f} | {t['r2']:<8.4f}"
        )
    print("-" * 78)
    print(f"Selected: {regressor_dict['best_model']}")
    print(f"Reason  : {regressor_dict['selection_reason']}")
    print(f"Baseline RMSE (Test): {regressor_dict['baseline_rmse']:.4f} LPA")
    print(
        f"Rows used: {regressor_dict['n_train_rows']} train / {regressor_dict['n_test_rows']} test"
    )

    elapsed = time.time() - start_time
    print("\n" + "=" * 78)
    print(f" TRAINING PIPELINE COMPLETED IN {elapsed:.2f} SECONDS")
    print("=" * 78)


if __name__ == "__main__":
    main()
