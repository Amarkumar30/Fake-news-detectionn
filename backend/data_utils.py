from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from config import DATA_FILES, DEFAULT_DATA_DIRECTORIES


LIAR_COLUMNS = [
    "id",
    "label",
    "statement",
    "subject",
    "speaker",
    "job",
    "state",
    "party",
    "barely_true_counts",
    "false_counts",
    "half_true_counts",
    "mostly_true_counts",
    "pants_on_fire_counts",
    "context",
]

LABEL_MAP = {
    "pants-fire": 0,
    "false": 0,
    "barely-true": 0,
    "half-true": 1,
    "mostly-true": 1,
    "true": 1,
}


def resolve_data_directory(explicit_data_dir: str | Path | None = None) -> Path:
    """Pick the first directory that contains the full LIAR split set."""
    candidate_directories: list[Path] = []

    if explicit_data_dir is not None:
        candidate_directories.append(Path(explicit_data_dir).expanduser().resolve())

    candidate_directories.extend(path.resolve() for path in DEFAULT_DATA_DIRECTORIES)

    for candidate in candidate_directories:
        if all((candidate / filename).exists() for filename in DATA_FILES.values()):
            return candidate

    checked_locations = "\n".join(f"- {directory}" for directory in candidate_directories)
    raise FileNotFoundError(
        "LIAR dataset files were not found. Place train.tsv, valid.tsv, and test.tsv in one of:\n"
        f"{checked_locations}"
    )


def _coerce_numeric_columns(frame: pd.DataFrame, numeric_columns: Iterable[str]) -> pd.DataFrame:
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)
    return frame


def _normalize_text_columns(frame: pd.DataFrame, text_columns: Iterable[str]) -> pd.DataFrame:
    for column in text_columns:
        frame[column] = frame[column].fillna("unknown").astype(str).str.strip()
        frame.loc[frame[column] == "", column] = "unknown"
    return frame


def load_liar_split(data_dir: str | Path, split_name: str) -> pd.DataFrame:
    split_path = Path(data_dir) / DATA_FILES[split_name]
    frame = pd.read_csv(split_path, sep="\t", header=None, names=LIAR_COLUMNS)
    return preprocess_liar_dataframe(frame)


def preprocess_liar_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame["label"] = frame["label"].map(LABEL_MAP)
    frame = frame.dropna(subset=["label", "statement"])
    frame["label"] = frame["label"].astype(int)

    numeric_columns = [
        "barely_true_counts",
        "false_counts",
        "half_true_counts",
        "mostly_true_counts",
        "pants_on_fire_counts",
    ]
    text_columns = ["statement", "subject", "speaker", "job", "state", "party", "context"]

    frame = _coerce_numeric_columns(frame, numeric_columns)
    frame = _normalize_text_columns(frame, text_columns)
    return frame.reset_index(drop=True)
