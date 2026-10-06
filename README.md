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
