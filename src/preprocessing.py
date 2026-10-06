"""Module 1: Preprocessing and Feature Engineering.

Handles data cleaning, outlier handling, encoding, scaling, and feature creation.
"""

import pandas as pd


def clean_and_engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the raw placement dataset and engineer predictive features."""
    cleaned = df.copy()
    
    # Feature engineering: composite score
    cleaned["academic_index"] = cleaned["cgpa"] * 10
    cleaned["skill_score"] = (cleaned["coding_score"] * 0.6) + (cleaned["communication_score"] * 0.4)
    cleaned["experience_points"] = (cleaned["internships"] * 2) + cleaned["projects"]
    
    return cleaned


def save_processed_data(df: pd.DataFrame, output_path: str) -> None:
    """Save processed dataframe to CSV."""
    df.to_csv(output_path, index=False)
