# Placement Analyzer & Prediction

An end-to-end Machine Learning and Data Science project to analyze placement readiness, predict placement outcomes and salary packages, identify skill gaps, and provide personalized career recommendations via an interactive Streamlit web application.

---

## 📁 Project Structure

```text
placement-analyzer/
│
├── data/
│   ├── raw/
│   │   └── placement_data.csv          # Generated synthetic dataset
│   └── processed/
│       └── clean_data.csv              # Cleaned + feature-engineered data
│
├── models/
│   ├── placement_model.pkl             # Best placement status classifier
│   ├── salary_model.pkl                # Best salary package regressor
│   └── metrics.json                    # Model comparison and evaluation metrics
│
├── notebooks/
│   ├── 01_EDA.ipynb                    # Exploratory Data Analysis
│   └── 02_Model_Training.ipynb         # Model training & experiment tracking
│
├── reports/
│   └── figures/                        # Saved EDA and feature importance plots
│
├── src/
│   ├── __init__.py
│   ├── config.py                       # Benchmarks, thresholds, paths, and role requirements
│   ├── data_generator.py               # Module 1: Synthetic data generator
│   ├── preprocessing.py                # Module 1: Cleaning and feature engineering pipeline
│   ├── train_models.py                 # Module 2: Model training, tuning, and evaluation
│   ├── predict.py                      # Module 2: Inference utilities
│   ├── skill_gap.py                    # Module 3: Skill gap analysis engine
│   ├── recommender.py                  # Module 3: Recommendation engine
│   └── charts.py                       # Module 4: Visualization and chart helpers
│
├── app.py                              # Module 4: Streamlit web application entry point
├── requirements.txt                    # Project dependencies
├── README.md                           # Documentation
└── .gitignore                          # Git ignore rules
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9+ installed

### 2. Installation
Create and activate a virtual environment:
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Running the Application
Launch the Streamlit dashboard:
```bash
streamlit run app.py
```
