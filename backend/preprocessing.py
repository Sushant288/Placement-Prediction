"""Module 1: Data Preprocessing and Feature Engineering.

Cleans raw placement data, imputes missing values, engineers domain-specific features,
and splits data into stratified train/test sets.
"""

from pathlib import Path
from typing import Any, Dict, List, Tuple, Union
import numpy as np
import pandas as pd

from backend.config import (
    BACKLOG_PENALTY,
    CLEAN_DATA_PATH,
    EXPERIENCE_COLS,
    EXPERIENCE_WEIGHTS,
    FEATURE_RANGES,
    MAX_EXPERIENCE_RAW,
    MODEL_FEATURES,
    RANDOM_SEED,
    RAW_DATA_PATH,
    RAW_FEATURES,
    SOFT_SKILL_COLS,
    TARGET_CLASS,
    TARGET_REG,
    TECH_SKILL_COLS,
    TEST_DATA_PATH,
    TEST_SIZE,
    TRAIN_DATA_PATH,
)


def load_raw_data(path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    """Load raw dataset from disk or trigger generator if file does not exist."""
    if not path.exists():
        print(f"Raw data file not found at {path}. Triggering data generator...")
        from backend.data_generator import main as generate_main
        generate_main()
    print(f"Loading raw data from {path}...")
    return pd.read_csv(path)


def validate_schema(df: pd.DataFrame) -> None:
    """Validate that all required raw feature columns and targets exist."""
    required_cols = RAW_FEATURES + [TARGET_CLASS, TARGET_REG]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(
            f"Schema validation failed. Missing required columns: {missing}"
        )


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean raw dataset by dropping duplicates, imputing missing values, and validating consistency.

    Note:
        Imputing missing values with the global median prior to train/test split
        is a minor design simplification for this module.
    """
    rows_initial = len(df)
    
    # 1. Drop exact duplicate rows
    df_clean = df.drop_duplicates().copy()
    duplicates_dropped = rows_initial - len(df_clean)

    # 2. Drop rows where targets are missing
    targets_valid = df_clean[TARGET_CLASS].notna() & df_clean[TARGET_REG].notna()
    missing_targets_dropped = int((~targets_valid).sum())
    df_clean = df_clean[targets_valid].copy()

    # 3. Fill missing values in feature columns with column median
    missing_filled: Dict[str, int] = {}
    for col in RAW_FEATURES:
        n_na = int(df_clean[col].isna().sum())
        if n_na > 0:
            median_val = df_clean[col].median()
            col_type = FEATURE_RANGES[col][2]
            fill_val = int(round(median_val)) if col_type == "int" else float(median_val)
            df_clean[col] = df_clean[col].fillna(fill_val)
            missing_filled[col] = n_na

    # 4. Clip features to valid ranges and cast to declared types
    clipped_counts = 0
    for col in RAW_FEATURES:
        min_v, max_v, col_type = FEATURE_RANGES[col]
        clipped_mask = (df_clean[col] < min_v) | (df_clean[col] > max_v)
        clipped_counts += int(clipped_mask.sum())
        df_clean[col] = df_clean[col].clip(lower=min_v, upper=max_v)
        if col_type == "int":
            df_clean[col] = df_clean[col].round().astype(int)
        else:
            df_clean[col] = df_clean[col].astype(float)

    # 5. Consistency check:
    # Set salary_lpa = 0 where placed == 0; drop rows where placed == 1 and salary_lpa <= 0
    inconsistent_mask = (df_clean[TARGET_CLASS] == 1) & (df_clean[TARGET_REG] <= 0)
    inconsistent_dropped = int(inconsistent_mask.sum())
    df_clean = df_clean[~inconsistent_mask].copy()

    df_clean.loc[df_clean[TARGET_CLASS] == 0, TARGET_REG] = 0.0
    df_clean[TARGET_CLASS] = df_clean[TARGET_CLASS].astype(int)
    df_clean[TARGET_REG] = df_clean[TARGET_REG].astype(float)

    rows_final = len(df_clean)

    # 6. Cleaning report
    print("--- Data Cleaning Report ---")
    print(f"Initial rows: {rows_initial} | Final rows: {rows_final}")
    print(f"Duplicates removed: {duplicates_dropped}")
    print(f"Missing targets dropped: {missing_targets_dropped}")
    print(f"Missing feature values imputed: {missing_filled}")
    print(f"Values clipped to schema range: {clipped_counts}")
    print(f"Inconsistent placed rows dropped: {inconsistent_dropped}")
    print("----------------------------")

    return df_clean


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer composite scores on 0-10 scale for academic, experience, tech, and soft skills."""
    df_out = df.copy()

    # tech_score: mean of technical skill assessments (1-10)
    df_out["tech_score"] = np.round(df_out[TECH_SKILL_COLS].mean(axis=1), 2)

    # soft_score: mean of communication and aptitude (1-10)
    df_out["soft_score"] = np.round(df_out[SOFT_SKILL_COLS].mean(axis=1), 2)

    # experience_score: weighted experience normalized to 0-10
    exp_raw = sum(df_out[col] * EXPERIENCE_WEIGHTS[col] for col in EXPERIENCE_COLS)
    df_out["experience_score"] = np.round(
        np.clip((exp_raw / MAX_EXPERIENCE_RAW) * 10.0, 0.0, 10.0), 2
    )

    # academic_score: cgpa with backlog penalty clipped to 0-10
    academic = df_out["cgpa"] - (BACKLOG_PENALTY * df_out["backlogs"])
    df_out["academic_score"] = np.round(np.clip(academic, 0.0, 10.0), 2)

    return df_out


def split_and_save(
    df: pd.DataFrame, test_size: float = TEST_SIZE, seed: int = RANDOM_SEED
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Perform stratified split on placement status and save train and test datasets."""
    from sklearn.model_selection import train_test_split

    cols_to_save = MODEL_FEATURES + [TARGET_CLASS, TARGET_REG]
    df_subset = df[cols_to_save].copy()

    train_df, test_df = train_test_split(
        df_subset,
        test_size=test_size,
        random_state=seed,
        stratify=df_subset[TARGET_CLASS],
    )

    TRAIN_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    train_df.to_csv(TRAIN_DATA_PATH, index=False)
    test_df.to_csv(TEST_DATA_PATH, index=False)

    print(f"Saved stratified train set ({len(train_df)} rows) to {TRAIN_DATA_PATH}")
    print(f"Saved stratified test set ({len(test_df)} rows) to {TEST_DATA_PATH}")
    return train_df, test_df


def run_pipeline() -> Dict[str, Any]:
    """Execute complete data preparation and preprocessing pipeline."""
    print("Starting preprocessing pipeline...")
    raw_df = load_raw_data()
    validate_schema(raw_df)
    clean_df = clean_data(raw_df)
    engineered_df = engineer_features(clean_df)

    cols_order = MODEL_FEATURES + [TARGET_CLASS, TARGET_REG]
    final_df = engineered_df[cols_order].copy()

    CLEAN_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(CLEAN_DATA_PATH, index=False)
    print(
        f"Saved clean engineered data ({len(final_df)} rows, {len(final_df.columns)} cols) to {CLEAN_DATA_PATH}"
    )

    train_df, test_df = split_and_save(final_df)

    placement_rate = float(final_df[TARGET_CLASS].mean())
    summary: Dict[str, Any] = {
        "rows": len(final_df),
        "placement_rate": round(placement_rate, 4),
        "train_rows": len(train_df),
        "test_rows": len(test_df),
    }
    print(f"Pipeline complete! Summary: {summary}")
    return summary


def load_clean_data() -> pd.DataFrame:
    """Load cleaned dataset from processed data directory."""
    if not CLEAN_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Clean data not found at {CLEAN_DATA_PATH}. Run python -m backend.preprocessing first."
        )
    return pd.read_csv(CLEAN_DATA_PATH)


def load_train_test() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load train and test datasets from processed data directory."""
    if not TRAIN_DATA_PATH.exists() or not TEST_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Train/test files not found at {TRAIN_DATA_PATH} or {TEST_DATA_PATH}. Run python -m backend.preprocessing first."
        )
    return pd.read_csv(TRAIN_DATA_PATH), pd.read_csv(TEST_DATA_PATH)


def preprocess_input(student: Dict[str, Any]) -> pd.DataFrame:
    """Convert a single candidate's feature dictionary into a 1-row engineered DataFrame."""
    # Check for missing required raw features
    missing_keys = [k for k in RAW_FEATURES if k not in student]
    if missing_keys:
        raise ValueError(
            f"Input is missing required raw features: {missing_keys}"
        )

    row_data: Dict[str, Union[int, float]] = {}
    for k in RAW_FEATURES:
        val = student[k]
        if not isinstance(val, (int, float, np.number)) or isinstance(val, bool):
            raise ValueError(
                f"Feature '{k}' must be numeric, got {type(val).__name__} ({val})"
            )
        min_v, max_v, col_type = FEATURE_RANGES[k]
        clipped_val = min(max(float(val), float(min_v)), float(max_v))
        if col_type == "int":
            row_data[k] = int(round(clipped_val))
        else:
            row_data[k] = float(clipped_val)

    single_df = pd.DataFrame([row_data])[RAW_FEATURES]
    eng_df = engineer_features(single_df)
    return eng_df[MODEL_FEATURES]


if __name__ == "__main__":
    summary_res = run_pipeline()
    print("Preprocessing completed successfully:", summary_res)
