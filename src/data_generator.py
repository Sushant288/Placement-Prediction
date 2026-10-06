"""Module 1: Synthetic Placement Data Generator.

Generates realistic synthetic student academic and placement records.
"""

import numpy as np
import pandas as pd


def generate_placement_data(n_samples: int = 1000, random_state: int = 42) -> pd.DataFrame:
    """Generate synthetic student placement records."""
    np.random.seed(random_state)
    
    student_ids = [f"STU{i:04d}" for i in range(1, n_samples + 1)]
    cgpa = np.round(np.clip(np.random.normal(7.2, 1.1, n_samples), 5.0, 10.0), 2)
    internships = np.random.choice([0, 1, 2, 3], size=n_samples, p=[0.35, 0.40, 0.20, 0.05])
    projects = np.random.choice([1, 2, 3, 4, 5], size=n_samples, p=[0.15, 0.35, 0.30, 0.15, 0.05])
    coding_score = np.round(np.clip(np.random.normal(68, 15, n_samples), 20, 100), 1)
    communication_score = np.round(np.clip(np.random.normal(70, 14, n_samples), 25, 100), 1)
    
    # Placement probability calculation
    score = (
        (cgpa / 10.0) * 0.35
        + (internships / 3.0) * 0.20
        + (projects / 5.0) * 0.15
        + (coding_score / 100.0) * 0.20
        + (communication_score / 100.0) * 0.10
    )
    prob = 1 / (1 + np.exp(-10 * (score - 0.55)))
    placed = (np.random.rand(n_samples) < prob).astype(int)
    
    # Salary calculation (LPA) for placed students
    base_salary = 3.5 + 0.8 * (cgpa - 5.0) + 1.2 * internships + 0.6 * projects + 0.05 * coding_score
    noise = np.random.normal(0, 0.8, n_samples)
    salary = np.where(placed == 1, np.round(np.clip(base_salary + noise, 3.0, 30.0), 2), 0.0)
    
    df = pd.DataFrame({
        "student_id": student_ids,
        "cgpa": cgpa,
        "internships": internships,
        "projects": projects,
        "coding_score": coding_score,
        "communication_score": communication_score,
        "placed": placed,
        "salary": salary,
    })
    return df


if __name__ == "__main__":
    from src.config import RAW_DATA_PATH
    RAW_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = generate_placement_data()
    data.to_csv(RAW_DATA_PATH, index=False)
    print(f"Generated {len(data)} samples and saved to {RAW_DATA_PATH}")
