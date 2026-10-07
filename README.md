# Placement Analyzer & Prediction

An end-to-end Machine Learning and Data Science project to analyze placement readiness, predict placement outcomes and salary packages, identify skill gaps, and provide personalized career recommendations via an interactive Streamlit web application.

---

## 📁 Project Structure

```text
placement-analyzer/
│
├── backend/
│   ├── __init__.py
│   ├── config.py                       # Configuration, benchmarks, thresholds, paths
│   ├── data_generator.py               # Module 1: Synthetic data generator
│   ├── preprocessing.py                # Module 1: Cleaning & feature engineering
│   ├── train_models.py                 # Module 2: Model training & evaluation
│   ├── predict.py                      # Module 2: Inference pipelines
│   ├── skill_gap.py                    # Module 3: Skill gap analysis engine
│   ├── recommender.py                  # Module 3: Recommendation engine
│   └── services.py                     # Service layer connecting backend modules
│
├── frontend/
│   ├── __init__.py
│   ├── charts.py                       # Module 4: Plotly visualization helpers
│   └── components.py                   # Module 4: UI layout and components
│
├── data/
│   ├── raw/
│   │   └── .gitkeep
│   └── processed/
│       └── .gitkeep
│
├── models/
│   └── .gitkeep
│
├── notebooks/
│   ├── 01_EDA.ipynb                    # Exploratory Data Analysis
│   └── 02_Model_Training.ipynb         # Model training & experiment tracking
│
├── reports/
│   └── figures/
│       └── .gitkeep
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

---

## 🔬 Module 1: Data Generation & Preprocessing

### Execution Order
Run the data pipeline from the repository root:
```bash
python -m backend.data_generator
python -m backend.preprocessing
```

### Generated Artifacts
- `data/raw/placement_data.csv`: Raw synthetic dataset (2,500 samples, 15 columns)
- `data/processed/clean_data.csv`: Cleaned, validated, and feature-engineered dataset (2,500 samples, 19 columns)
- `data/processed/train.csv`: Stratified training set (2,000 samples, 80%)
- `data/processed/test.csv`: Stratified evaluation set (500 samples, 20%)
- `reports/figures/*.png`: Exploratory data analysis charts generated from `notebooks/01_EDA.ipynb`

> [!NOTE]
> The current dataset is synthetically generated using calibrated latent ability/effort factors and empirical hiring relationships. The entire end-to-end pipeline operates seamlessly on real-world placement data by placing an institutional dataset with matching schema into `data/raw/placement_data.csv`.

---

## 🤖 Module 2: Machine Learning Models

### Execution Order
Execute model training and test prediction from the repository root:
```bash
python -m backend.train_models
python -m backend.predict
```
Execute the experimentation notebook:
```bash
python -m nbconvert --to notebook --execute --inplace notebooks/02_Model_Training.ipynb
```

### Generated Artifacts
- `models/placement_model.pkl`: Serialized best placement classification Pipeline (`StandardScaler` + `LogisticRegression`)
- `models/salary_model.pkl`: Serialized best conditional salary regression Pipeline (`StandardScaler` + `LinearRegression`)
- `models/metrics.json`: Comprehensive 5-fold CV and holdout test evaluation metrics, hyperparameter grids, and permutation importances
- `reports/figures/model_comparison_classifier.png`: Test set performance metrics across candidate classifiers
- `reports/figures/roc_curves.png`: Receiver operating characteristic curves for all candidate classifiers
- `reports/figures/confusion_matrix.png`: Confusion matrix for the chosen placement classifier
- `reports/figures/calibration_curve.png`: Reliability diagram comparing predicted probabilities against empirical frequencies
- `reports/figures/feature_importance_classifier.png`: Top 12 permutation feature importances for placement classification
- `reports/figures/model_comparison_regressor.png`: MAE and RMSE comparison across salary regression candidates
- `reports/figures/salary_actual_vs_predicted.png`: Actual vs. predicted salary scatter plot for placed students
- `reports/figures/feature_importance_regressor.png`: Top 12 permutation feature importances for salary regression
- `reports/figures/probability_sweep_dsa.png`: Sensitivity sweep demonstrating monotonic placement probability growth

### Model Selection Rule (Leakage-Free)
- **Leakage Prevention**: All model training, hyperparameter optimization, and pipeline selection rely strictly on `train.csv`. The `test.csv` partition is evaluated only once at the conclusion for unbiased metric reporting.
- **Placement Classifier**: Evaluated using Stratified 5-Fold Cross-Validation. Any model with CV ROC-AUC within `MODEL_SELECTION_AUC_TOLERANCE` (0.005) of the maximum is considered tied; ties are broken by the lowest CV Brier score (best probability calibration).
- **Salary Regressor**: Evaluated using 5-Fold Cross-Validation strictly on placed students (`placed == 1`). Selected by the lowest CV RMSE.

### Readiness Score & Risk Level Thresholds
- **Readiness Score (0-100)**:
  $$\text{Readiness} = 100 \times \left(0.50 \cdot P(\text{placed}) + 0.25 \cdot \frac{\text{tech\_score}}{10} + 0.15 \cdot \frac{\text{soft\_score}}{10} + 0.10 \cdot \frac{\text{experience\_score}}{10}\right)$$
- **Risk Level Thresholds**:
  - **LOW**: $\text{probability} \ge 0.75$
  - **MEDIUM**: $0.45 \le \text{probability} < 0.75$
  - **HIGH**: $\text{probability} < 0.45$

---

## 🎯 Module 3: Skill Gap & Recommendation Engine

### Execution Order
Run the skill gap assessment and recommendation engine from the repository root:
```bash
python -m backend.skill_gap
python -m backend.recommender
```

### Roles & Benchmarks
The system evaluates students against three specialized industry profiles:
1. **Software Developer**: Core emphasis on DSA (importance 3.0) and Programming (importance 3.0), supported by Web, SQL, Cloud, Communication, and Aptitude.
2. **Data Analyst**: Heavy focus on SQL (importance 3.0) and Communication (importance 3.0), supported by Programming, Aptitude, Cloud, and DSA.
3. **Data Scientist**: Comprehensive mathematical and engineering profile prioritizing Programming (importance 3.0), Aptitude (importance 3.0), and SQL (importance 2.5).

### Skill Status & Prioritization Rules
- **Status Classification**:
  - **GOOD**: $\text{score} \ge \text{benchmark}$ ($\text{gap} \le 0$)
  - **MODERATE**: $0 < \text{gap} \le 2$ points below benchmark
  - **WEAK**: $\text{gap} > 2$ points below benchmark
- **Priority Formula**:
  $$\text{Priority Score} = \text{gap} \times \text{role\_importance}$$
  Skills are ordered by descending priority score, directing student effort toward areas with the highest career payoff.

### Public API Functions
- **`backend.skill_gap`**:
  - `list_roles() -> List[str]`: Enumerate available career tracks.
  - `get_role_profile(role) -> dict`: Retrieve benchmark thresholds and importance weights.
  - `get_skill_status(score, benchmark) -> str`: Return GOOD, MODERATE, or WEAK status.
  - `analyze_skills(student, role) -> dict`: Full breakdown of gaps, surpluses, role fit percentage, and profile checks.
  - `get_improvement_targets(student, role) -> Dict[str, float]`: Benchmark targets for deficient features.
  - `get_radar_data(student, role) -> dict`: Structured radar chart payload.
- **`backend.recommender`**:
  - `compute_impact_analysis(student, role) -> List[dict]`: Quantify probability gain for single-feature improvements.
  - `get_recommendations(student, role, max_items, include_impact) -> List[dict]`: Actionable, prioritized coaching items.
  - `simulate_improvement(student, changes) -> dict`: What-if simulation evaluating arbitrary metric adjustments.
  - `simulate_reaching_benchmark(student, role, include_profile) -> dict`: Simulate reaching role benchmark requirements.


