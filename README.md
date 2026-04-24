# ============================================================
#   FAKE NEWS DETECTION | LIAR DATASET | FLASK + REACT + ML
# ============================================================

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Flask-API-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/React-Vite-61DAFB?style=for-the-badge&logo=react&logoColor=0D1117" alt="React" />
  <img src="https://img.shields.io/badge/scikit--learn-ML-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white" alt="scikit-learn" />
</p>

## Problem Statement
Misinformation spreads faster than manual fact-checking can keep up, especially when claims are short, emotional, and detached from context. This project builds an end-to-end fake news detection system on the LIAR dataset, combining interpretable NLP features, metadata-driven credibility signals, a Flask inference API, and a React analysis interface.

## Repository Structure
```text
fake-news-detector/
├── backend/              # Flask API, training pipeline, persisted ML artifacts
├── frontend/             # React + Vite investigation-style web UI
├── notebooks/            # EDA and training/evaluation notebooks
├── report/               # CVPR-style LaTeX report
├── tests/                # Pytest suite for the API
└── .github/workflows/    # GitHub Actions CI
```

## Architecture
```text
                   +----------------------+
                   |   LIAR train/valid   |
                   |      /test TSVs      |
                   +----------+-----------+
                              |
                              v
                   +----------------------+
                   |  Preprocessing +     |
                   |  Feature Engineering |
                   |  - TF-IDF            |
                   |  - Speaker score     |
                   |  - Party / subject   |
                   +----------+-----------+
                              |
          +-------------------+-------------------+
          |                   |                   |
          v                   v                   v
 +----------------+  +----------------+  +----------------------+
 | Logistic Reg.  |  |  Naive Bayes   |  | Random Forest        |
 | TF-IDF baseline|  | TF-IDF baseline|  | TF-IDF + metadata    |
 +--------+-------+  +--------+-------+  +----------+-----------+
          \                   |                     /
           \                  |                    /
            +-----------------+-------------------+
                              |
                              v
                   +----------------------+
                   | Flask API            |
                   | /health /stats       |
                   | /predict             |
                   +----------+-----------+
                              |
                              v
                   +----------------------+
                   | React + Vite Frontend|
                   | Detector / About /   |
                   | Research pages       |
                   +----------------------+
```

## Tech Stack
- Backend: Python, Flask, pandas, NumPy, scikit-learn, NLTK, joblib
- Frontend: React 18, Vite, React Router, Axios, Recharts, Framer Motion
- Analysis: Jupyter, matplotlib, seaborn, wordcloud
- Reporting: LaTeX (CVPR-style format)

## Quick Start
### 1. Clone the repository
```bash
git clone <your-repo-url>
cd fake-news-detector
```

### 2. Install backend dependencies
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

### 3. Install frontend dependencies
```bash
cd frontend
npm install
cd ..
```

### 4. Download the LIAR dataset
Download `train.tsv`, `valid.tsv`, and `test.tsv` from the LIAR dataset source:
- Hugging Face dataset page: <https://huggingface.co/datasets/UKPLab/liar>
- Original paper: \`"Liar, Liar Pants on Fire"\`

Place the files in one of the following locations:
```text
data/
backend/data/
```

### 5. Train the models
```bash
cd backend
python train.py --data-dir ../data
cd ..
```

### 6. Run the backend API
```bash
cd backend
python app.py
```
Backend default URL: `http://localhost:5000`

### 7. Run the frontend
```bash
cd frontend
npm run dev
```
Frontend default URL: `http://localhost:3000`

## API Documentation
Base URL: `http://localhost:5000`

### `GET /api/health`
Health check for the Flask service.

Example response:
```json
{
  "status": "ready",
  "deployed_model": "RandomForest",
  "available_models": ["LogisticRegression", "NaiveBayes", "RandomForest"],
  "startup_error": null
}
```

### `GET /api/stats`
Returns persisted training and evaluation metadata.

Example response:
```json
{
  "trained_at_utc": "2026-04-25T00:00:00+00:00",
  "dataset_sizes": {
    "train": 10269,
    "valid": 1284,
    "test": 1283
  },
  "deployed_model": "RandomForest",
  "best_validation_model": "RandomForest",
  "models": {
    "LogisticRegression": {
      "validation": { "accuracy": 0.0, "f1_score": 0.0 },
      "test": { "accuracy": 0.0, "f1_score": 0.0 }
    }
  }
}
```

### `POST /api/predict`
Analyze a claim and return a binary fake/real prediction.

Request body:
```json
{
  "text": "The senator says unemployment is at its lowest level in fifty years.",
  "speaker": "campaign spokesperson",
  "party": "democrat"
}
```

Example response:
```json
{
  "prediction": "REAL",
  "confidence": 0.87,
  "model": "RandomForest",
  "explanation": {
    "top_tfidf_features": [
      { "feature": "unemployment", "contribution": 0.0912 },
      { "feature": "lowest level", "contribution": 0.0741 }
    ],
    "explanation_method": "importance_weighted_tfidf",
    "credibility_score": 0.63,
    "text_statistics": {
      "text_length": 68.0,
      "punctuation_count": 1.0,
      "all_caps_ratio": 0.0,
      "exclamation_count": 0.0
    }
  }
}
```

Example error response:
```json
{
  "error": "The 'text' field is required and cannot be empty."
}
```

## Model Performance
Replace the placeholders below with the values exported by `notebooks/results.json` after training.

| Model | Features | Accuracy | F1 Score | Notes |
|---|---|---:|---:|---|
| Logistic Regression | TF-IDF (1,2)-gram | TBD | TBD | Strong linear baseline |
| Naive Bayes | TF-IDF (1,2)-gram | TBD | TBD | Fast sparse probabilistic baseline |
| Random Forest | TF-IDF + credibility + metadata | TBD | TBD | Best production candidate |

## Screenshots
Add generated screenshots after running the frontend locally.

```text
report/figures/
frontend/public/
README assets/
```

Suggested screenshots:
- Home detector page
- Prediction result card
- About page metrics charts
- Research page

## Dataset Citation
If you use this project or dataset setup, please cite:

> Wang, W. Y. 2017. "Liar, Liar Pants on Fire": A New Benchmark Dataset for Fake News Detection. ACL.

Dataset reference:
- LIAR benchmark: <https://aclanthology.org/P17-2067/>

## Testing and CI
This repository includes:
- `pytest` API tests in `tests/test_api.py`
- `flake8` linting for backend and tests
- GitHub Actions workflow in `.github/workflows/test.yml`

Run locally:
```bash
python -m pytest tests
flake8 backend tests
```

## Author
**Project Maintainer:** Replace with your name, affiliation, and contact information.

Suggested format:
```text
Your Name
Department / Organization
Email: your.email@example.com
GitHub: https://github.com/your-handle
```
