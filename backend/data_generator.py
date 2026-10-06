"""Module 1: Synthetic Data Generation.

Generates realistic student placement records with academic, skill, and outcome variables.
"""

from typing import Optional
import numpy as np
import pandas as pd

from backend.config import (
    INJECT_MISSING,
    MISSING_COLUMNS,
    MISSING_RATE,
    N_STUDENTS,
    RANDOM_SEED,
    RAW_DATA_PATH,
    RAW_FEATURES,
    TARGET_PLACEMENT_RATE,
)


def generate_dataset(
    n_students: int = N_STUDENTS,
    seed: int = RANDOM_SEED,
    inject_missing: bool = INJECT_MISSING,
) -> pd.DataFrame:
    """Generate synthetic placement dataset using latent factors and domain relationships."""
    rng = np.random.default_rng(seed)

    # Step 1: Latent variables per student
    ability = rng.normal(0.0, 1.0, size=n_students)
    effort = rng.normal(0.0, 1.0, size=n_students)

    # Step 2: Academic, experience, and skill features
    cgpa = np.clip(
        np.round(7.0 + 0.7 * ability + 0.3 * effort + rng.normal(0.0, 0.5, size=n_students), 2),
        5.0,
        10.0,
    )
    backlogs = np.clip(
        rng.poisson(np.maximum(0.02, 0.7 - 0.4 * (cgpa - 7.0))),
        0,
        5,
    ).astype(int)
    attendance = np.clip(
        np.round(rng.normal(78.0 + 3.0 * effort + 2.0 * (cgpa - 7.0), 8.0, size=n_students)),
        50,
        100,
    ).astype(int)
    internships = np.clip(
        rng.poisson(np.maximum(0.05, 0.8 + 0.4 * ability + 0.3 * effort)),
        0,
        3,
    ).astype(int)
    projects = np.clip(
        rng.poisson(np.maximum(0.1, 2.2 + 0.7 * ability + 0.5 * effort)),
        0,
        6,
    ).astype(int)
    certifications = np.clip(
        rng.poisson(np.maximum(0.1, 1.3 + 0.4 * effort + 0.3 * ability)),
        0,
        5,
    ).astype(int)

    # Tech skills
    dsa = np.clip(
        np.round(5.0 + 1.0 * ability + 0.8 * effort + 0.0 + rng.normal(0.0, 1.2, size=n_students)),
        1,
        10,
    ).astype(int)
    programming = np.clip(
        np.round(5.0 + 1.0 * ability + 0.8 * effort + 0.5 + rng.normal(0.0, 1.2, size=n_students)),
        1,
        10,
    ).astype(int)
    sql = np.clip(
        np.round(5.0 + 1.0 * ability + 0.8 * effort + 0.0 + rng.normal(0.0, 1.2, size=n_students)),
        1,
        10,
    ).astype(int)
    cloud = np.clip(
        np.round(5.0 + 1.0 * ability + 0.8 * effort - 1.2 + rng.normal(0.0, 1.2, size=n_students)),
        1,
        10,
    ).astype(int)
    web = np.clip(
        np.round(5.0 + 1.0 * ability + 0.8 * effort + 0.0 + rng.normal(0.0, 1.2, size=n_students)),
        1,
        10,
    ).astype(int)

    # Soft skills
    communication = np.clip(
        np.round(5.3 + 0.5 * ability + 0.6 * effort + rng.normal(0.0, 1.4, size=n_students)),
        1,
        10,
    ).astype(int)
    aptitude = np.clip(
        np.round(5.5 + 0.8 * ability + 0.2 * effort + rng.normal(0.0, 1.3, size=n_students)),
        1,
        10,
    ).astype(int)

    # Step 3: Placement (logistic model)
    z = (
        0.9 * (cgpa - 7.0)
        - 0.7 * backlogs
        + 0.02 * (attendance - 75.0)
        + 0.55 * internships
        + 0.30 * projects
        + 0.15 * certifications
        + 0.30 * (dsa - 5.0)
        + 0.25 * (programming - 5.0)
        + 0.10 * (sql - 5.0)
        + 0.08 * (cloud - 5.0)
        + 0.08 * (web - 5.0)
        + 0.18 * (communication - 5.0)
        + 0.15 * (aptitude - 5.0)
        + rng.normal(0.0, 0.6, size=n_students)
    )

    def sigmoid(val: np.ndarray) -> np.ndarray:
        return 1.0 / (1.0 + np.exp(-val))

    # Bisection search for intercept b0 to match TARGET_PLACEMENT_RATE
    low, high = -10.0, 10.0
    b0 = 0.0
    for _ in range(100):
        mid = (low + high) / 2.0
        rate = float(np.mean(sigmoid(z + mid)))
        if abs(rate - TARGET_PLACEMENT_RATE) < 0.0001:
            b0 = mid
            break
        if rate < TARGET_PLACEMENT_RATE:
            low = mid
        else:
            high = mid
    else:
        b0 = (low + high) / 2.0

    probs = sigmoid(z + b0)
    placed = (rng.uniform(0.0, 1.0, size=n_students) < probs).astype(int)

    # Step 4: Salary (LPA) only for placed candidates, 0.0 otherwise
    base = (
        3.2
        + 0.45 * (dsa - 5.0)
        + 0.35 * (programming - 5.0)
        + 0.15 * (sql - 5.0)
        + 0.15 * (cloud - 5.0)
        + 0.10 * (web - 5.0)
        + 0.80 * internships
        + 0.25 * projects
        + 0.60 * (cgpa - 7.0)
        + 0.12 * (communication - 5.0)
    )
    base = np.maximum(base, 1.5)
    salary_raw = base * rng.lognormal(mean=0.0, sigma=0.15, size=n_students)

    outlier_prob = np.where(dsa >= 8, 0.08, 0.01)
    is_outlier = rng.uniform(0.0, 1.0, size=n_students) < outlier_prob
    multiplier = np.where(is_outlier, rng.uniform(1.4, 2.2, size=n_students), 1.0)
    salary = salary_raw * multiplier
    salary_lpa = np.where(placed == 1, np.clip(np.round(salary, 2), 3.0, 30.0), 0.0)

    # Assemble DataFrame with exact RAW_FEATURES order
    data_dict = {
        "cgpa": cgpa,
        "backlogs": backlogs,
        "attendance": attendance,
        "internships": internships,
        "projects": projects,
        "certifications": certifications,
        "dsa": dsa,
        "programming": programming,
        "sql": sql,
        "cloud": cloud,
        "web": web,
        "communication": communication,
        "aptitude": aptitude,
        "placed": placed,
        "salary_lpa": salary_lpa,
    }
    df = pd.DataFrame(data_dict)

    cols_order = RAW_FEATURES + ["placed", "salary_lpa"]
    df = df[cols_order]

    # Step 5: Missing-value injection
    if inject_missing:
        n_missing = int(round(n_students * MISSING_RATE))
        for col in MISSING_COLUMNS:
            missing_idx = rng.choice(n_students, size=n_missing, replace=False)
            df.loc[missing_idx, col] = np.nan

    return df


def main() -> None:
    """Generate dataset and save to raw data directory."""
    print(f"Generating synthetic placement data (n={N_STUDENTS}, seed={RANDOM_SEED})...")
    df = generate_dataset()
    RAW_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_DATA_PATH, index=False)
    print(f"Successfully saved raw dataset with {len(df)} rows and {len(df.columns)} columns to {RAW_DATA_PATH}")


if __name__ == "__main__":
    main()
