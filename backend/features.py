from __future__ import annotations

import re
import string
from typing import Iterable

import numpy as np
import pandas as pd
from nltk.stem import SnowballStemmer
from nltk.tokenize import wordpunct_tokenize
from scipy import sparse
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder


STEMMER = SnowballStemmer("english")
ALPHA_PATTERN = re.compile(r"^[A-Za-z]+$")
NUMERIC_FEATURE_NAMES = [
    "speaker_credibility",
    "text_length",
    "punctuation_count",
    "all_caps_ratio",
    "exclamation_count",
]


def normalize_string(value: object, default: str = "unknown") -> str:
    if value is None:
        return default
    normalized = str(value).strip()
    return normalized or default


def tokenize_statement(text: str) -> list[str]:
    """NLTK-backed tokenizer for the TF-IDF vectorizer."""
    tokens: list[str] = []
    for token in wordpunct_tokenize(normalize_string(text, default="")):
        lowered = token.lower()
        if not ALPHA_PATTERN.match(lowered):
            continue
        if lowered in ENGLISH_STOP_WORDS:
            continue
        stemmed = STEMMER.stem(lowered)
        if len(stemmed) > 1:
            tokens.append(stemmed)
    return tokens


def split_subjects(subject_text: str) -> list[str]:
    normalized = normalize_string(subject_text)
    parts = [part.strip().lower() for part in normalized.split(",") if part.strip()]
    return parts or ["unknown"]


def calculate_credibility_from_counts(row: pd.Series) -> float:
    total = (
        float(row["barely_true_counts"])
        + float(row["false_counts"])
        + float(row["half_true_counts"])
        + float(row["mostly_true_counts"])
        + float(row["pants_on_fire_counts"])
    )
    if total <= 0:
        return 0.5

    penalty = (float(row["false_counts"]) + float(row["pants_on_fire_counts"])) / total
    return float(np.clip(1.0 - penalty, 0.0, 1.0))


def build_speaker_lookup(train_frame: pd.DataFrame) -> tuple[dict[str, float], float]:
    scored_frame = train_frame.copy()
    scored_frame["speaker_credibility"] = scored_frame.apply(calculate_credibility_from_counts, axis=1)

    speaker_scores = (
        scored_frame.groupby("speaker")["speaker_credibility"].mean().sort_values(ascending=False).to_dict()
    )
    default_score = float(scored_frame["speaker_credibility"].mean())
    return speaker_scores, default_score


def compute_text_statistics(text: str) -> dict[str, float]:
    normalized = normalize_string(text, default="")
    tokens = [token for token in wordpunct_tokenize(normalized) if token.strip()]
    alphabetical_tokens = [token for token in tokens if any(character.isalpha() for character in token)]
    all_caps_tokens = [token for token in alphabetical_tokens if token.isupper() and len(token) > 1]

    return {
        "text_length": float(len(normalized)),
        "punctuation_count": float(sum(1 for character in normalized if character in string.punctuation)),
        "all_caps_ratio": float(len(all_caps_tokens) / max(len(alphabetical_tokens), 1)),
        "exclamation_count": float(normalized.count("!")),
    }


def build_numeric_feature_matrix(
    frame: pd.DataFrame,
    speaker_scores: dict[str, float],
    default_speaker_score: float,
) -> sparse.csr_matrix:
    credibility_values = [
        float(speaker_scores.get(normalize_string(speaker), default_speaker_score))
        for speaker in frame["speaker"].tolist()
    ]

    text_statistics = frame["statement"].apply(compute_text_statistics)
    feature_rows = np.column_stack(
        [
            np.asarray(credibility_values, dtype=np.float64),
            text_statistics.map(lambda item: item["text_length"]).to_numpy(dtype=np.float64),
            text_statistics.map(lambda item: item["punctuation_count"]).to_numpy(dtype=np.float64),
            text_statistics.map(lambda item: item["all_caps_ratio"]).to_numpy(dtype=np.float64),
            text_statistics.map(lambda item: item["exclamation_count"]).to_numpy(dtype=np.float64),
        ]
    )
    return sparse.csr_matrix(feature_rows, dtype=np.float64)


def build_tfidf_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(
        tokenizer=tokenize_statement,
        token_pattern=None,
        lowercase=False,
        max_features=10_000,
        ngram_range=(1, 2),
    )


def build_party_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=True)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=True)


def build_subject_vectorizer() -> CountVectorizer:
    return CountVectorizer(
        tokenizer=split_subjects,
        token_pattern=None,
        lowercase=True,
        binary=True,
    )


def combine_engineered_features(
    tfidf_matrix: sparse.csr_matrix,
    numeric_matrix: sparse.csr_matrix,
    party_matrix: sparse.csr_matrix,
    subject_matrix: sparse.csr_matrix,
) -> sparse.csr_matrix:
    return sparse.hstack([tfidf_matrix, numeric_matrix, party_matrix, subject_matrix], format="csr")


def get_engineered_feature_names(
    text_feature_names: Iterable[str],
    party_feature_names: Iterable[str],
    subject_feature_names: Iterable[str],
) -> list[str]:
    return (
        list(text_feature_names)
        + NUMERIC_FEATURE_NAMES
        + list(party_feature_names)
        + list(subject_feature_names)
    )
