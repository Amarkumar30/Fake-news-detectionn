# TruthLens Setup Guide by amar

<a id="prerequisites"></a>
## Prerequisites

TruthLens is a full-stack fake news detection application with a Python/Flask machine-learning backend and a React/Vite frontend. Install the following before running it locally.

| Requirement | Version | Notes |
|---|---:|---|
| Python | 3.9+ | Python 3.11 is recommended. Use `pyenv` or `pyenv-win` if you switch between projects. |
| Node.js | 18+ | Use `nvm` or `nvm-windows` to avoid global Node version conflicts. |
| Git | Current stable | Needed to clone the repository and work with branches. |
| RAM | 4 GB minimum | Training uses pandas, TF-IDF matrices, and scikit-learn models. |
| Disk space | 2 GB free | Covers dependencies, dataset files, generated models, and frontend build artifacts. |

Useful version checks:

```bash
python --version
node --version
npm --version
git --version
```

<a id="quick-start"></a>
## Quick Start

> Replace `<repo-url>` with the actual repository URL before pasting.

1. Clone and enter the repository.

```bash
git clone <repo-url> truthlens
cd truthlens
```

2. Install Python and JavaScript dependencies.

```bash
make install
```

3. Download the LIAR dataset into `data/`.

The Hugging Face dataset loader for `ucsbnlp/liar` uses the official LIAR archive published by the dataset author. This command downloads that archive and extracts `train.tsv`, `valid.tsv`, and `test.tsv` into the folder expected by TruthLens.

```bash
mkdir -p data
curl -L https://www.cs.ucsb.edu/~william/data/liar_dataset.zip -o data/liar_dataset.zip
python -m zipfile -e data/liar_dataset.zip data
```

If you prefer `wget`:

```bash
mkdir -p data
wget -O data/liar_dataset.zip https://www.cs.ucsb.edu/~william/data/liar_dataset.zip
python -m zipfile -e data/liar_dataset.zip data
```

4. Train the local models.

```bash
make train
```

Training usually takes about 2-3 minutes on a laptop. The terminal prints a JSON summary with dataset sizes, validation/test metrics, the deployed model name, and the path where model artifacts were saved.

5. Start the full development stack.

```bash
make dev
```

Open these URLs:

| Service | URL |
|---|---|
| React frontend | `http://localhost:3000` |
| Flask health check | `http://localhost:5000/api/health` |
| Model statistics | `http://localhost:5000/api/stats` |

<a id="directory-structure"></a>
## Directory Structure

```text
truthlens/
|-- .github/
|   `-- workflows/
|       `-- test.yml                  # GitHub Actions workflow for backend linting and tests.
|-- backend/
|   |-- app.py                        # Flask app factory and API route definitions.
|   |-- config.py                     # Runtime configuration, paths, environment variables, and constants.
|   |-- data_utils.py                 # LIAR TSV loading, column naming, label mapping, and cleanup.
|   |-- features.py                   # Text normalization, tokenization, TF-IDF, and metadata feature builders.
|   |-- feedback.json                 # Local JSON feedback store written by `/api/feedback`.
|   |-- gunicorn.conf.py              # Production Gunicorn configuration for the Flask app.
|   |-- model_service.py              # Training, artifact persistence, model loading, prediction, and explanations.
|   |-- requirements.txt              # Python dependencies for API, training, tests, and deployment.
|   |-- train.py                      # CLI entry point for training and saving models.
|   |-- logs/                         # Generated Flask and prediction logs; safe to delete.
|   |-- models/
|   |   |-- logistic_regression.pkl    # Generated Logistic Regression artifact.
|   |   |-- naive_bayes.pkl            # Generated Naive Bayes artifact.
|   |   |-- random_forest.pkl          # Generated Random Forest artifact used by default.
|   |   `-- training_summary.json      # Generated metrics and training metadata.
|   `-- tests/
|       `-- test_integration.py       # Optional live-server integration tests against localhost Flask.
|-- data/
|   |-- train.tsv                     # LIAR training split.
|   |-- valid.tsv                     # LIAR validation split.
|   `-- test.tsv                      # LIAR test split.
|-- frontend/
|   |-- .env.local                    # Local frontend environment variables.
|   |-- .env.production               # Production frontend environment template.
|   |-- index.html                    # Vite HTML entry point.
|   |-- package.json                  # Frontend scripts and dependencies.
|   |-- package-lock.json             # Locked npm dependency graph.
|   |-- vite.config.js                # Vite and React plugin configuration.
|   |-- dist/                         # Generated production frontend build; safe to delete.
|   |-- node_modules/                 # Generated npm dependencies; safe to delete.
|   |-- public/                       # Static assets served by Vite.
|   |-- scripts/
|   |   `-- windows-safe-cli.mjs       # Wrapper for reliable Vite/Vitest execution on Windows.
|   `-- src/
|       |-- api/client.js             # Axios client and backend API wrappers.
|       |-- app/App.jsx               # Route definitions and backend health banner state.
|       |-- components/               # Reusable UI components for results, charts, layout, and status.
|       |-- data/                     # Static example statements and research references.
|       |-- pages/                    # Detector, About, Research, and Health pages.
|       |-- styles/index.css          # Global frontend styling.
|       |-- test/setup.js             # Vitest/JSDOM test setup.
|       `-- __tests__/App.test.jsx    # Frontend smoke and rendering tests.
|-- notebooks/
|   |-- eda.ipynb                     # Exploratory LIAR dataset analysis notebook.
|   `-- train_evaluate.ipynb          # Notebook workflow for training and evaluation experiments.
|-- report/
|   |-- main.tex                      # Academic-style project report source.
|   `-- references.bib                # Bibliography entries for the report.
|-- tests/
|   `-- test_api.py                   # Fast Flask API unit tests with a mocked model service.
|-- .flake8                           # Python linting rules.
|-- .gitignore                        # Files excluded from version control.
|-- ARCHITECTURE.md                   # Technical system and ML architecture deep dive.
|-- Makefile                          # Main developer commands: install, train, dev, test, build, clean.
|-- README.md                         # Project overview.
|-- SETUP.md                          # This setup guide.
|-- pytest.ini                        # Pytest configuration.
|-- start.bat                         # Windows startup helper.
`-- start.sh                          # Unix startup helper.
```

Generated folders such as `frontend/node_modules/`, `frontend/dist/`, `backend/logs/`, `.pytest_cache/`, and `__pycache__/` are rebuildable and are removed by `make clean`.

<a id="dataset"></a>
## Dataset

TruthLens uses the LIAR benchmark dataset introduced by William Yang Wang in the ACL 2017 short paper, `"Liar, Liar Pants on Fire": A New Benchmark Dataset for Fake News Detection`. The Hugging Face dataset card is `ucsbnlp/liar`, and its loader references the original archive at `https://www.cs.ucsb.edu/~william/data/liar_dataset.zip`.

Citation:

```bibtex
@inproceedings{wang-2017-liar,
  title = "{``}Liar, Liar Pants on Fire{''}: A New Benchmark Dataset for Fake News Detection",
  author = "Wang, William Yang",
  booktitle = "Proceedings of the 55th Annual Meeting of the Association for Computational Linguistics (Volume 2: Short Papers)",
  year = "2017",
  pages = "422--426",
  doi = "10.18653/v1/P17-2067"
}
```

### Binary Label Mapping

LIAR is originally a six-class truthfulness dataset. TruthLens converts it into a binary classifier:

| LIAR label | TruthLens label | Numeric value |
|---|---|---:|
| `pants-fire` | `FAKE` | `0` |
| `false` | `FAKE` | `0` |
| `barely-true` | `FAKE` | `0` |
| `half-true` | `REAL` | `1` |
| `mostly-true` | `REAL` | `1` |
| `true` | `REAL` | `1` |

This mapping is implemented in `backend/data_utils.py` as `LABEL_MAP`.

### File Format

Each LIAR split is a tab-separated values file with no header row. TruthLens reads the files with `pandas.read_csv(..., sep="\t", header=None)`.

Expected columns:

| Position | Column | Description |
|---:|---|---|
| 0 | `id` | LIAR statement identifier. |
| 1 | `label` | Original six-way truthfulness label. |
| 2 | `statement` | Political claim or short statement. |
| 3 | `subject` | Topic tags such as economy, health, or education. |
| 4 | `speaker` | Person or organization making the claim. |
| 5 | `job` | Speaker job title. |
| 6 | `state` | Speaker state information. |
| 7 | `party` | Political party affiliation. |
| 8 | `barely_true_counts` | Speaker history count for barely true claims. |
| 9 | `false_counts` | Speaker history count for false claims. |
| 10 | `half_true_counts` | Speaker history count for half true claims. |
| 11 | `mostly_true_counts` | Speaker history count for mostly true claims. |
| 12 | `pants_on_fire_counts` | Speaker history count for most severe false claims. |
| 13 | `context` | Venue or context where the claim appeared. |

<a id="running-tests"></a>
## Running Tests

Run all configured tests:

```bash
make test
```

What runs:

| Test area | Command run by `make test` | What it checks |
|---|---|---|
| Backend unit/API tests | `python -m pytest tests backend/tests -q` | Flask route behavior, validation errors, feedback persistence, model response shape, live API behavior when Flask is already running. |
| Frontend tests | `cd frontend && npm run test` | React rendering, route-level smoke behavior, and test setup under Vitest/JSDOM. |

A passing backend run looks similar to:

```text
.......                                                                  [100%]
7 passed, 7 skipped in 3.42s
```

Some integration tests in `backend/tests/test_integration.py` skip automatically if a live Flask server is not running at `http://127.0.0.1:5000`.

A passing frontend run looks similar to:

```text
Test Files  1 passed
Tests       1 passed
```

<a id="common-errors-and-fixes"></a>
## Common Errors & Fixes

| Error | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'flask'` | Python dependencies were not installed in the active environment. | Run `make install`. If using a virtual environment, activate it first and run `python -m pip install -r backend/requirements.txt`. |
| `ModuleNotFoundError: No module named 'model_service'` | Backend modules are being imported from the wrong working directory. | Run backend commands through the Makefile, or run `cd backend && python app.py`. For tests, use `python -m pytest tests backend/tests -q` from the repo root. |
| `LIAR dataset files were not found` | `train.tsv`, `valid.tsv`, and `test.tsv` are missing. | Download the dataset into `data/` and confirm `data/train.tsv`, `data/valid.tsv`, and `data/test.tsv` exist. |
| Model files not found | `backend/models/*.pkl` and `training_summary.json` are missing. | Run `make train`. `make dev` also runs `ensure-models` and trains automatically if artifacts are absent. |
| Browser CORS error | The frontend is calling a backend origin not listed in Flask CORS settings. | Use `VITE_API_URL=http://localhost:5000` and open the frontend at `http://localhost:3000`. If using another host, add that origin to `API_ALLOWED_ORIGINS` in `backend/config.py`. |
| `Address already in use` or port conflict | Port `3000` or `5000` is already occupied. | Stop the existing process. For Flask, set a different port with `FLASK_PORT=5001`. For Vite, run `cd frontend && npm run dev -- --port 3001`. |
| Dataset TSV parse error | The extracted files are corrupted, have headers added, or are not tab-separated. | Re-download the official archive, extract it cleanly, and keep the original headerless TSV files. Do not open and re-save them in spreadsheet software. |
| `npm ERR! enoent Could not read package.json` | npm was run from the repository root instead of `frontend/`. | Use `make install`, or run `cd frontend && npm install`. |
| `npx: command not found` | Node.js/npm is not installed or not on `PATH`. | Install Node.js 18+ with `nvm`/`nvm-windows`, then reopen the terminal and check `node --version`. |
| NLTK download prompt or tokenizer issue | The project uses `wordpunct_tokenize` and Snowball stemming, which do not require downloading `punkt`. A different local script may be importing another tokenizer. | Run the official training path with `make train`. If you added custom NLTK tokenizers, install the required corpus with `python -m nltk.downloader <resource>`. |
| Windows `make` is not recognized | GNU Make is not installed. | Install Make through Git Bash, Chocolatey, MSYS2, or WSL. Alternatively run the commands in the `Makefile` manually. |

<a id="environment-variables"></a>
## Environment Variables

| Name | Default | Description | Required? |
|---|---|---|---|
| `MODEL_DIR` | `backend/models/` | Directory where backend model artifacts and `training_summary.json` are loaded from or written to. Relative paths resolve from `backend/`. | No |
| `FAKE_NEWS_DEPLOYED_MODEL` | `RandomForest` | Model name used for live predictions when available. Valid artifact names are `LogisticRegression`, `NaiveBayes`, and `RandomForest`. | No |
| `FLASK_ENV` | `production` | Set to `development` for Flask debug mode through `config.IS_DEVELOPMENT`. | No |
| `FLASK_PORT` | `5000` | Port used when running `backend/app.py`. | No |
| `LOG_LEVEL` | `INFO` | Python logging level for prediction audit logging. | No |
| `VITE_API_URL` | `http://localhost:5000` | Frontend API base URL used by `frontend/src/api/client.js`. | No |
| `VITE_APP_NAME` | `TruthLens` in env files | Frontend app name placeholder for deployment metadata or future UI use. | No |

The backend loads environment variables from `backend/.env` if present. The frontend uses Vite env files such as `frontend/.env.local` and `frontend/.env.production`.

<a id="resetting-everything"></a>
## Resetting Everything

Use `make clean` to remove generated Python caches, frontend dependencies/build output, pytest caches, and backend logs:

```bash
make clean
```

Then rebuild from a clean local state:

```bash
make install
make train
make dev
```

`make clean` does not remove `data/` or `backend/models/`. To retrain from scratch, delete the generated files in `backend/models/` manually and run `make train` again.
