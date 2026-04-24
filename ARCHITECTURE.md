# TruthLens Architecture

<a id="project-overview"></a>
## Project Overview

TruthLens is a fake news detection system that classifies short political claims as `REAL` or `FAKE`. It combines TF-IDF text features, speaker credibility signals, and metadata from the LIAR benchmark, then serves predictions through a Flask API and a React investigation interface. The application is designed as a portfolio-quality, end-to-end ML product rather than a notebook-only classifier.

TruthLens is useful for academics evaluating baseline misinformation models, journalists experimenting with claim triage workflows, and curious users who want to inspect how a lightweight NLP classifier reasons about political statements.

Current limitations are important: LIAR is mostly political and PolitiFact-derived, so the model does not generalize automatically to every news domain. The original six-label task is noisy and subjective, and traditional TF-IDF plus classical ML baselines commonly hit an accuracy ceiling around 70-75% on realistic full-size LIAR experiments. TruthLens should be treated as decision support, not as an automated fact-checker.

<a id="system-architecture"></a>
## System Architecture

```text
+---------+      +----------------+      +-------------+      +----------------+      +----------------+
| Browser | ---> | React + Vite   | ---> | Flask API   | ---> | ML Artifacts   | ---> | JSON Response  |
|         |      | axios client   |      | /api/*      |      | joblib models  |      | verdict + expl |
+---------+      +----------------+      +-------------+      +----------------+      +----------------+
```

### Request Lifecycle

1. The user types a claim into the detector form and optionally adds speaker and party metadata.
2. The user clicks `Analyze`, which validates the form in `frontend/src/pages/DetectorPage.jsx`.
3. The frontend calls `predictNews(payload)` in `frontend/src/api/client.js`.
4. Axios sends a `POST` request to `VITE_API_URL + /api/predict`.
5. Flask receives the request in `backend/app.py`.
6. `FakeNewsDetectionService._validate_payload()` checks JSON shape, text length, and optional metadata.
7. The service builds the inference feature matrix: TF-IDF text features, text statistics, speaker credibility, party encoding, and subject vectorization.
8. The deployed scikit-learn model runs `predict_proba()`.
9. The highest-probability class becomes `REAL` or `FAKE`; its probability becomes the confidence score.
10. The backend builds an explanation from active TF-IDF terms and returns JSON.
11. The React UI stores the response in local state and renders the result panel, confidence display, credibility gauge, and keyword chips.

<a id="tech-stack"></a>
## Tech Stack

| Layer | Technology | Version | Why this choice |
|---|---|---:|---|
| Frontend | React | 18.3.1 | Component model, broad ecosystem, predictable state flow. |
| Frontend | Vite | 6.3.5 | Fast dev server, ES modules, simple production builds. |
| Frontend | Framer Motion | 12.6.3 | Polished page and panel transitions without custom animation plumbing. |
| Frontend | Axios | 1.8.4 | Clear request wrappers, timeout handling, and response/error normalization. |
| Backend | Flask | 3.1.0 | Lightweight, ML-friendly API layer with minimal framework overhead. |
| Backend | scikit-learn | 1.6.1 | Mature, well-documented classical ML toolkit with reliable persistence via joblib. |
| Backend | NLTK | 3.9.1 | Text tokenization and stemming utilities for preprocessing. |
| Backend | pandas | 2.2.3 | TSV loading, cleanup, and feature assembly. |
| ML | TF-IDF | scikit-learn | Strong sparse text baseline for short claim classification. |
| ML | Logistic Regression | scikit-learn | Interpretable linear baseline with calibrated class probabilities. |
| ML | Naive Bayes | scikit-learn | Fast probabilistic sparse-text baseline. |
| ML | Random Forest | scikit-learn | Tree ensemble that can combine sparse text features with metadata features. |
| Data | LIAR Dataset | 2017 | Political statements with truthfulness labels, speaker metadata, and historical counts. |

Note: this repository currently deploys `RandomForest` by default. A Gradient Boosting model would be a reasonable next experiment, but it is not the current persisted model in `backend/model_service.py`.

<a id="ml-pipeline"></a>
## ML Pipeline

### Text Preprocessing

The text pipeline is implemented in `backend/features.py`.

```text
Raw text
  -> normalize to string
  -> tokenize with NLTK wordpunct_tokenize
  -> lowercase each token
  -> remove non-alphabetic tokens and punctuation
  -> remove English stopwords
  -> stem with SnowballStemmer
  -> emit tokens into TF-IDF
```

The code does not separately call a punctuation-removal function; punctuation is filtered by accepting only alphabetic tokens with `ALPHA_PATTERN`.

### TF-IDF Vectorization

TruthLens uses:

```python
TfidfVectorizer(
    tokenizer=tokenize_statement,
    token_pattern=None,
    lowercase=False,
    max_features=10000,
    ngram_range=(1, 2),
)
```

`max_features=10000` keeps the sparse feature space large enough to capture meaningful political vocabulary while preventing unnecessary memory growth.

`ngram_range=(1, 2)` includes unigrams and bigrams. Bigrams help preserve short phrases such as `tax cut`, `health care`, or `climate change`, which can carry more signal than the same words treated independently.

### Feature Engineering

The deployed Random Forest receives TF-IDF plus engineered metadata features:

```text
full_features = [tfidf_features, numeric_features, party_one_hot, subject_binary_tags]
```

Numeric meta-features:

| Feature | Source |
|---|---|
| `speaker_credibility` | Mean credibility estimate from the speaker's LIAR history. |
| `text_length` | Character count of the input claim. |
| `punctuation_count` | Number of punctuation characters. |
| `all_caps_ratio` | Ratio of uppercase word tokens to alphabetic word tokens. |
| `exclamation_count` | Number of exclamation marks. |

Speaker credibility formula:

```text
total_history =
  barely_true_counts
+ false_counts
+ half_true_counts
+ mostly_true_counts
+ pants_on_fire_counts

false_penalty =
  (false_counts + pants_on_fire_counts) / total_history

speaker_credibility =
  clip(1.0 - false_penalty, 0.0, 1.0)
```

If a speaker has no history, the score defaults to `0.5`. For unseen speakers at inference time, the model uses the mean credibility score learned from the training split.

### Model Training

Training is coordinated by `LiarModelTrainer.train_and_persist()` in `backend/model_service.py`.

| Model | Features | Purpose |
|---|---|---|
| `LogisticRegression` | TF-IDF | Strong, interpretable linear baseline. |
| `NaiveBayes` | TF-IDF | Very fast sparse-text baseline. |
| `RandomForest` | TF-IDF + metadata | Current deployed model; combines text with speaker, party, subject, and numeric signals. |

The tree ensemble can outperform pure text baselines when metadata helps separate similar claims. LIAR includes speaker history, party, subject, and context-like signals, so a model that can use non-text features has an advantage over text-only baselines. Classical ensembles still have limits on sparse text problems, which is why transformer models are listed in the roadmap.

### Prediction and Confidence

At inference time, the loaded model returns probabilities:

```python
probabilities = artifact["model"].predict_proba(feature_matrix)[0]
predicted_index = int(np.argmax(probabilities))
confidence = float(probabilities[predicted_index])
prediction = "REAL" if predicted_index == 1 else "FAKE"
```

The API rounds confidence to four decimals in the JSON response. A confidence of `0.82` means the selected class received 82% of the model's probability mass, not that the statement is objectively 82% true.

### Explainability

TruthLens extracts the active TF-IDF features for the input text and ranks them:

| Model family | Explanation approach |
|---|---|
| Logistic Regression | Active TF-IDF values multiplied by signed class coefficients. |
| Naive Bayes | Active TF-IDF values multiplied by class log-probability differences. |
| Random Forest | Active TF-IDF values multiplied by global feature importances. |

For Random Forest, the explanation is approximate because scikit-learn Random Forest does not expose exact local feature attribution without additional libraries. The returned keywords are best read as influential terms the model recognized, not as a formal causal explanation.

<a id="api-design"></a>
## API Design

Base URL in local development:

```text
http://localhost:5000
```

### `GET /api/health`

Reports backend readiness and loaded model state.

Response schema:

```json
{
  "status": "ok",
  "deployed_model": "RandomForest",
  "available_models": ["LogisticRegression", "NaiveBayes", "RandomForest"],
  "loaded_model_count": 3,
  "startup_error": null
}
```

Error codes:

| Status | Meaning |
|---:|---|
| 200 | Health payload returned. `status` may still be `degraded` if model loading failed. |

Example:

```bash
curl http://localhost:5000/api/health
```

### `GET /api/stats`

Returns training metadata and evaluation metrics from `backend/models/training_summary.json`.

Response schema:

```json
{
  "trained_at_utc": "2026-04-24T20:12:49.357621+00:00",
  "data_directory": "data",
  "dataset_sizes": {
    "train": 10269,
    "valid": 1284,
    "test": 1283
  },
  "deployed_model": "RandomForest",
  "best_validation_model": "RandomForest",
  "models": {
    "RandomForest": {
      "validation": {
        "accuracy": 0.72,
        "precision": 0.73,
        "recall": 0.71,
        "f1_score": 0.72,
        "roc_auc": 0.78,
        "confusion_matrix": [[300, 100], [95, 330]]
      },
      "test": {
        "accuracy": 0.71,
        "precision": 0.72,
        "recall": 0.70,
        "f1_score": 0.71,
        "roc_auc": 0.77,
        "confusion_matrix": [[295, 105], [100, 325]]
      }
    }
  }
}
```

Error codes:

| Status | Meaning |
|---:|---|
| 200 | Training statistics are available. |
| 503 | No training summary was loaded. |

Example:

```bash
curl http://localhost:5000/api/stats
```

### `GET /api/models`

Returns artifact inventory for known model files.

Response schema:

```json
{
  "models": [
    {
      "name": "RandomForest",
      "file_name": "random_forest.pkl",
      "loaded": true,
      "size_bytes": 123456,
      "path": "backend/models/random_forest.pkl"
    }
  ],
  "models_dir": "backend/models"
}
```

Error codes:

| Status | Meaning |
|---:|---|
| 200 | Inventory returned. Individual models may have `"loaded": false`. |

Example:

```bash
curl http://localhost:5000/api/models
```

### `POST /api/predict`

Classifies one claim and returns a model explanation.

Request schema:

```json
{
  "text": "The budget office reported that tax receipts increased compared with the previous fiscal year.",
  "speaker": "budget office",
  "party": "nonpartisan",
  "subject": "economy"
}
```

Required fields:

| Field | Required | Notes |
|---|---|---|
| `text` | Yes | Must be non-empty and at least 10 characters. Text longer than 5000 characters is truncated. |
| `speaker` | No | Defaults to `unknown`. Enables speaker credibility when supplied. |
| `party` | No | Defaults to `unknown`. |
| `subject` | No | Defaults to `unknown`. The current frontend does not send this field, but the API supports it. |

Response schema:

```json
{
  "prediction_id": "e4a7c9d2f6b64a4c8c55a9f4a7e8f212",
  "prediction": "REAL",
  "confidence": 0.8732,
  "model": "RandomForest",
  "explanation": {
    "top_tfidf_features": [
      {
        "feature": "budget",
        "contribution": 0.0412
      }
    ],
    "explanation_method": "importance_weighted_tfidf",
    "credibility_score": 0.6125,
    "text_statistics": {
      "text_length": 86.0,
      "punctuation_count": 1.0,
      "all_caps_ratio": 0.0,
      "exclamation_count": 0.0
    }
  }
}
```

Error codes:

| Status | Meaning |
|---:|---|
| 400 | Invalid JSON, empty text, text too short, or invalid request body. |
| 429 | Rate limit exceeded; currently `30 per minute`. |
| 503 | Model service is not ready. |
| 500 | Unexpected server error. |

Example:

```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The budget office reported that tax receipts increased compared with the previous fiscal year.",
    "speaker": "budget office",
    "party": "nonpartisan",
    "subject": "economy"
  }'
```

### `POST /api/feedback`

Stores user feedback about a prediction in `backend/feedback.json`.

Request schema:

```json
{
  "prediction_id": "e4a7c9d2f6b64a4c8c55a9f4a7e8f212",
  "correct": true
}
```

Response schema:

```json
{
  "status": "saved",
  "feedback": {
    "prediction_id": "e4a7c9d2f6b64a4c8c55a9f4a7e8f212",
    "correct": true
  }
}
```

Error codes:

| Status | Meaning |
|---:|---|
| 201 | Feedback saved. |
| 400 | Request body is invalid, `prediction_id` is missing, or `correct` is not boolean. |
| 429 | Rate limit exceeded; currently `30 per minute`. |
| 500 | Unexpected server error. |

Example:

```bash
curl -X POST http://localhost:5000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "prediction_id": "e4a7c9d2f6b64a4c8c55a9f4a7e8f212",
    "correct": true
  }'
```

<a id="frontend-architecture"></a>
## Frontend Architecture

### Component Tree

```text
main.jsx
`-- BrowserRouter
    `-- App
        |-- Layout
        |   |-- navigation
        |   `-- backend health banner
        |-- Routes
        |   |-- DetectorPage
        |   |   |-- detector form
        |   |   |-- StatusMessage
        |   |   `-- ResultPanel
        |   |       |-- CircularConfidence
        |   |       |-- CredibilityGauge
        |   |       `-- KeywordChips
        |   |-- AboutPage
        |   |   |-- MetricsCharts
        |   |   `-- ModelComparisonTable
        |   |-- ResearchPage
        |   |   `-- research paper cards
        |   `-- HealthPage
        |       `-- backend/model status panels
        `-- PageTransition wrappers
```

### State Management

TruthLens uses local React state instead of Redux. The app has shallow state boundaries: detector form values, loading/error state, backend health status, and the latest prediction result. These states are local to one or two components, so a global store would add more ceremony than value.

### Environment Variables

`frontend/src/api/client.js` reads:

```js
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";
```

Local development uses `frontend/.env.local`:

```text
VITE_API_URL=http://localhost:5000
VITE_APP_NAME=TruthLens
```

Production builds can use `frontend/.env.production` or deployment platform variables:

```text
VITE_API_URL=https://your-api-domain.com
VITE_APP_NAME=TruthLens
```

### Health Check Banner

`App.jsx` runs `fetchBackendHealth()` on mount. While the request is pending, the layout displays `Checking backend connection...`. If the backend returns `status: "ok"`, the banner disappears. If the request fails or the backend reports a degraded startup state, the UI displays an error banner with a `Retry` button that calls the health check again.

<a id="data-flow"></a>
## Data Flow

### Training Data Flow

```text
LIAR TSV files
  -> pandas.read_csv
  -> preprocess_liar_dataframe
  -> binary LABEL_MAP
  -> tokenize_statement
  -> TF-IDF fit on train statements
  -> speaker credibility lookup from train metadata
  -> party one-hot encoder fit
  -> subject CountVectorizer fit
  -> model.fit
  -> joblib.dump artifacts
  -> backend/models/
```

### Prediction Data Flow

```text
HTTP request JSON
  -> Flask route /api/predict
  -> payload validation
  -> joblib-loaded artifact
  -> TF-IDF transform
  -> metadata feature transform
  -> predict_proba
  -> explanation assembly
  -> JSON response
```

<a id="model-performance"></a>
## Model Performance

The exact numbers depend on whether you train on the full official LIAR data or on a small local/sample split. After `make train`, the authoritative metrics are written to `backend/models/training_summary.json` and returned by `GET /api/stats`.

Example full-dataset target table:

| Model | Accuracy | Precision | Recall | F1 | Training Time |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | 0.68-0.73 | 0.68-0.74 | 0.68-0.74 | 0.68-0.73 | < 1 min |
| Naive Bayes | 0.60-0.68 | 0.60-0.69 | 0.60-0.69 | 0.60-0.68 | < 30 sec |
| Random Forest | 0.68-0.75 | 0.68-0.75 | 0.68-0.75 | 0.68-0.75 | 2-3 min |

Use the generated stats for resume or report claims:

```bash
curl http://localhost:5000/api/stats
```

### Why LIAR Is Hard

LIAR uses six fine-grained labels: `pants-fire`, `false`, `barely-true`, `half-true`, `mostly-true`, and `true`. Adjacent labels can be subjective even for humans, and TruthLens compresses them into a binary label for product usability. The dataset also contains short political statements where the truth often depends on external evidence, not just language. Speaker metadata helps, but it can be noisy because historical credibility does not prove whether a new claim is true.

### Accuracy Improvements

Likely next steps for stronger performance:

| Improvement | Why it helps |
|---|---|
| BERT or RoBERTa fine-tuning | Contextual embeddings capture semantics better than sparse TF-IDF. |
| DeBERTa or modern sentence transformers | Stronger language understanding on short claims. |
| Gradient Boosting over engineered features | Often stronger than Random Forest on tabular metadata. |
| Multimodal credibility network | Incorporates speaker, source, topic, and publication network signals. |
| Retrieval-augmented fact checking | Pulls external evidence instead of relying only on claim wording. |
| Calibration analysis | Makes confidence scores more trustworthy for user-facing decisions. |

<a id="production-roadmap"></a>
## Production Roadmap

To move TruthLens from localhost to a live deployment:

1. Backend: replace the Flask development server with Gunicorn and deploy the API on Render, Railway, Fly.io, or EC2. The repository already includes `backend/gunicorn.conf.py`.
2. Frontend: run `npm run build` and deploy `frontend/dist/` on Vercel, Netlify, Cloudflare Pages, or another static host.
3. Database: replace `backend/feedback.json` with PostgreSQL for durable feedback storage and queryability.
4. Auth: add API key authentication or user authentication before exposing write endpoints publicly.
5. Model versioning: use MLflow or simple versioned model directories such as `backend/models/v1/`, `backend/models/v2/`.
6. CI/CD: GitHub Actions already runs backend linting and tests; add frontend tests, build validation, and deployment steps.
7. Observability: record request IDs, latency, model version, prediction distribution, and structured error logs.
8. Safety: add clear user-facing disclaimers, abuse limits, and monitoring for adversarial inputs.

<a id="contributing"></a>
## Contributing

### Add a New Model

1. Edit `backend/model_service.py`.
2. Add the model to `MODEL_FILE_NAMES` in `backend/config.py`.
3. Train it in `LiarModelTrainer.train_and_persist()`.
4. Persist an artifact with the same keys expected by `FakeNewsDetectionService`.
5. Add evaluation metrics to the training summary.
6. Add or update tests in `tests/test_api.py` and, when needed, `backend/tests/test_integration.py`.
7. Run `make train` and `make test`.

### Retrain on New Data

New data must match the LIAR TSV schema or be converted before training.

```bash
make clean
make install
make train
```

If the new files are in another directory:

```bash
cd backend
python train.py --data-dir ../path/to/new-data --models-dir models
```

Then verify:

```bash
make test
curl http://localhost:5000/api/stats
```

### Code Style

| Area | Standard |
|---|---|
| Python | PEP 8 with project-specific `.flake8` settings: `max-line-length = 140`, `E203` and `W503` ignored. |
| Tests | Prefer focused pytest tests for API behavior, validation, and response shape. |
| React | Keep components small, route-level state local, and API calls isolated in `frontend/src/api/client.js`. |
| Frontend linting | Add an ESLint config before enforcing React lint rules in CI; the current repository uses Vitest but does not include an ESLint config yet. |
| Formatting | Keep generated files, caches, `node_modules`, and build output out of source control. |

Before opening a pull request or sharing the project:

```bash
make test
make build
```
