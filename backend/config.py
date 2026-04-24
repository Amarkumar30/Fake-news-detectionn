from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(BASE_DIR / ".env")


def _resolve_path_from_env(variable_name: str, default_value: str) -> Path:
    raw_value = os.getenv(variable_name, default_value)
    candidate_path = Path(raw_value)
    if not candidate_path.is_absolute():
        candidate_path = BASE_DIR / candidate_path
    return candidate_path.resolve()


MODELS_DIR = _resolve_path_from_env("MODEL_DIR", "models/")
LOGS_DIR = BASE_DIR / "logs"
PREDICTIONS_LOG_PATH = LOGS_DIR / "predictions.log"
FEEDBACK_PATH = BASE_DIR / "feedback.json"

DEFAULT_DATA_DIRECTORIES = [
    BASE_DIR / "data",
    PROJECT_ROOT / "data",
]

DATA_FILES = {
    "train": "train.tsv",
    "valid": "valid.tsv",
    "test": "test.tsv",
}

MODEL_FILE_NAMES = {
    "LogisticRegression": "logistic_regression.pkl",
    "NaiveBayes": "naive_bayes.pkl",
    "RandomForest": "random_forest.pkl",
}

METADATA_FILE_NAME = "training_summary.json"
DEPLOYED_MODEL_NAME = os.getenv("FAKE_NEWS_DEPLOYED_MODEL", "RandomForest")

FLASK_ENV = os.getenv("FLASK_ENV", "production").lower()
IS_DEVELOPMENT = FLASK_ENV == "development"
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
MAX_INPUT_TEXT_LENGTH = 5_000
MIN_INPUT_TEXT_LENGTH = 10

API_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
