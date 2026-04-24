from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.naive_bayes import MultinomialNB

from config import (
    DEPLOYED_MODEL_NAME,
    MAX_INPUT_TEXT_LENGTH,
    METADATA_FILE_NAME,
    MIN_INPUT_TEXT_LENGTH,
    MODEL_FILE_NAMES,
    MODELS_DIR,
)
from data_utils import load_liar_split, resolve_data_directory
from features import (
    NUMERIC_FEATURE_NAMES,
    build_numeric_feature_matrix,
    build_party_encoder,
    build_speaker_lookup,
    build_subject_vectorizer,
    build_tfidf_vectorizer,
    combine_engineered_features,
    compute_text_statistics,
    get_engineered_feature_names,
    normalize_string,
)


class ApiError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass
class PredictionResult:
    prediction_id: str
    prediction: str
    confidence: float
    model: str
    explanation: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "prediction": self.prediction,
            "confidence": round(self.confidence, 4),
            "model": self.model,
            "explanation": self.explanation,
        }


class LiarModelTrainer:
    def __init__(self, models_dir: str | Path | None = None) -> None:
        self.models_dir = Path(models_dir or MODELS_DIR).resolve()
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def train_and_persist(self, data_dir: str | Path | None = None) -> dict[str, Any]:
        resolved_data_dir = resolve_data_directory(data_dir)
        datasets = {split_name: load_liar_split(resolved_data_dir, split_name) for split_name in ("train", "valid", "test")}

        train_frame = datasets["train"]
        valid_frame = datasets["valid"]
        test_frame = datasets["test"]

        speaker_scores, default_speaker_score = build_speaker_lookup(train_frame)

        baseline_tfidf = build_tfidf_vectorizer()
        X_train_text = baseline_tfidf.fit_transform(train_frame["statement"])
        X_valid_text = baseline_tfidf.transform(valid_frame["statement"])
        X_test_text = baseline_tfidf.transform(test_frame["statement"])

        y_train = train_frame["label"].to_numpy(dtype=int)
        y_valid = valid_frame["label"].to_numpy(dtype=int)
        y_test = test_frame["label"].to_numpy(dtype=int)

        logistic_model = LogisticRegression(
            max_iter=2_000,
            class_weight="balanced",
            solver="liblinear",
            random_state=42,
        )
        logistic_model.fit(X_train_text, y_train)

        naive_bayes_model = MultinomialNB(alpha=0.5)
        naive_bayes_model.fit(X_train_text, y_train)

        engineered_tfidf = build_tfidf_vectorizer()
        X_train_engineered_text = engineered_tfidf.fit_transform(train_frame["statement"])
        X_valid_engineered_text = engineered_tfidf.transform(valid_frame["statement"])
        X_test_engineered_text = engineered_tfidf.transform(test_frame["statement"])

        party_encoder = build_party_encoder()
        X_train_party = party_encoder.fit_transform(train_frame[["party"]])
        X_valid_party = party_encoder.transform(valid_frame[["party"]])
        X_test_party = party_encoder.transform(test_frame[["party"]])

        subject_vectorizer = build_subject_vectorizer()
        X_train_subject = subject_vectorizer.fit_transform(train_frame["subject"])
        X_valid_subject = subject_vectorizer.transform(valid_frame["subject"])
        X_test_subject = subject_vectorizer.transform(test_frame["subject"])

        X_train_numeric = build_numeric_feature_matrix(train_frame, speaker_scores, default_speaker_score)
        X_valid_numeric = build_numeric_feature_matrix(valid_frame, speaker_scores, default_speaker_score)
        X_test_numeric = build_numeric_feature_matrix(test_frame, speaker_scores, default_speaker_score)

        X_train_engineered = combine_engineered_features(
            X_train_engineered_text, X_train_numeric, X_train_party, X_train_subject
        )
        X_valid_engineered = combine_engineered_features(
            X_valid_engineered_text, X_valid_numeric, X_valid_party, X_valid_subject
        )
        X_test_engineered = combine_engineered_features(
            X_test_engineered_text, X_test_numeric, X_test_party, X_test_subject
        )

        random_forest_model = RandomForestClassifier(
            n_estimators=300,
            max_depth=30,
            min_samples_leaf=2,
            class_weight="balanced_subsample",
            n_jobs=1,
            random_state=42,
        )
        random_forest_model.fit(X_train_engineered, y_train)

        logistic_artifact = {
            "model_name": "LogisticRegression",
            "model": logistic_model,
            "tfidf_vectorizer": baseline_tfidf,
            "text_feature_names": baseline_tfidf.get_feature_names_out().tolist(),
            "speaker_scores": speaker_scores,
            "default_speaker_score": default_speaker_score,
        }

        naive_bayes_artifact = {
            "model_name": "NaiveBayes",
            "model": naive_bayes_model,
            "tfidf_vectorizer": baseline_tfidf,
            "text_feature_names": baseline_tfidf.get_feature_names_out().tolist(),
            "speaker_scores": speaker_scores,
            "default_speaker_score": default_speaker_score,
        }

        engineered_feature_names = get_engineered_feature_names(
            engineered_tfidf.get_feature_names_out(),
            party_encoder.get_feature_names_out(["party"]),
            subject_vectorizer.get_feature_names_out(),
        )

        random_forest_artifact = {
            "model_name": "RandomForest",
            "model": random_forest_model,
            "tfidf_vectorizer": engineered_tfidf,
            "party_encoder": party_encoder,
            "subject_vectorizer": subject_vectorizer,
            "text_feature_names": engineered_tfidf.get_feature_names_out().tolist(),
            "engineered_feature_names": engineered_feature_names,
            "speaker_scores": speaker_scores,
            "default_speaker_score": default_speaker_score,
            "numeric_feature_names": NUMERIC_FEATURE_NAMES,
        }

        model_stats = {
            "LogisticRegression": self._evaluate_artifact(logistic_artifact, X_valid_text, y_valid, X_test_text, y_test),
            "NaiveBayes": self._evaluate_artifact(naive_bayes_artifact, X_valid_text, y_valid, X_test_text, y_test),
            "RandomForest": self._evaluate_artifact(
                random_forest_artifact, X_valid_engineered, y_valid, X_test_engineered, y_test
            ),
        }

        self._save_artifact(logistic_artifact)
        self._save_artifact(naive_bayes_artifact)
        self._save_artifact(random_forest_artifact)

        best_validation_model = max(model_stats, key=lambda name: model_stats[name]["validation"]["f1_score"])
        training_summary = {
            "trained_at_utc": datetime.now(timezone.utc).isoformat(),
            "data_directory": str(resolved_data_dir),
            "dataset_sizes": {split_name: int(len(frame)) for split_name, frame in datasets.items()},
            "deployed_model": DEPLOYED_MODEL_NAME if DEPLOYED_MODEL_NAME in model_stats else best_validation_model,
            "best_validation_model": best_validation_model,
            "models": model_stats,
        }

        summary_path = self.models_dir / METADATA_FILE_NAME
        summary_path.write_text(json.dumps(training_summary, indent=2), encoding="utf-8")
        return training_summary

    def _save_artifact(self, artifact: dict[str, Any]) -> None:
        output_path = self.models_dir / MODEL_FILE_NAMES[artifact["model_name"]]
        joblib.dump(artifact, output_path)

    def _evaluate_artifact(
        self,
        artifact: dict[str, Any],
        X_valid: sparse.csr_matrix,
        y_valid: np.ndarray,
        X_test: sparse.csr_matrix,
        y_test: np.ndarray,
    ) -> dict[str, Any]:
        return {
            "validation": self._compute_metrics(artifact["model"], X_valid, y_valid),
            "test": self._compute_metrics(artifact["model"], X_test, y_test),
        }

    @staticmethod
    def _compute_metrics(model: Any, features: sparse.csr_matrix, labels: np.ndarray) -> dict[str, Any]:
        predictions = model.predict(features)
        probabilities = model.predict_proba(features)[:, 1]
        try:
            roc_auc = round(float(roc_auc_score(labels, probabilities)), 4)
        except ValueError:
            roc_auc = None

        return {
            "accuracy": round(float(accuracy_score(labels, predictions)), 4),
            "precision": round(float(precision_score(labels, predictions, zero_division=0)), 4),
            "recall": round(float(recall_score(labels, predictions, zero_division=0)), 4),
            "f1_score": round(float(f1_score(labels, predictions, zero_division=0)), 4),
            "roc_auc": roc_auc,
            "confusion_matrix": confusion_matrix(labels, predictions).tolist(),
        }


class FakeNewsDetectionService:
    def __init__(self, models_dir: str | Path | None = None, data_dir: str | Path | None = None) -> None:
        self.models_dir = Path(models_dir or MODELS_DIR).resolve()
        self.data_dir = Path(data_dir).resolve() if data_dir else None
        self.models: dict[str, dict[str, Any]] = {}
        self.training_summary: dict[str, Any] = {}
        self.loaded_model_files: dict[str, Path] = {}
        self.ready = False
        self.startup_error: str | None = None
        self.deployed_model_name: str | None = None
        self._load_or_train()

    def _load_or_train(self) -> None:
        try:
            if not self._artifacts_exist():
                trainer = LiarModelTrainer(models_dir=self.models_dir)
                trainer.train_and_persist(data_dir=self.data_dir)

            loaded_models: dict[str, dict[str, Any]] = {}
            loaded_model_files: dict[str, Path] = {}
            for model_name, file_name in MODEL_FILE_NAMES.items():
                artifact_path = self.models_dir / file_name
                if artifact_path.exists():
                    loaded_models[model_name] = joblib.load(artifact_path)
                    loaded_model_files[model_name] = artifact_path

            self.models = loaded_models
            self.loaded_model_files = loaded_model_files
            summary_path = self.models_dir / METADATA_FILE_NAME
            if summary_path.exists():
                self.training_summary = json.loads(summary_path.read_text(encoding="utf-8"))

            if not self.models:
                raise RuntimeError("No trained model artifacts are available.")

            requested_model = self.training_summary.get("deployed_model", DEPLOYED_MODEL_NAME)
            self.deployed_model_name = requested_model if requested_model in self.models else next(iter(self.models))
            self.ready = True
            self.startup_error = None
        except Exception as exc:
            self.ready = False
            self.startup_error = str(exc)

    def _artifacts_exist(self) -> bool:
        summary_exists = (self.models_dir / METADATA_FILE_NAME).exists()
        model_files_exist = all((self.models_dir / file_name).exists() for file_name in MODEL_FILE_NAMES.values())
        return summary_exists and model_files_exist

    def health(self) -> dict[str, Any]:
        status = "ok" if self.ready else "degraded"
        return {
            "status": status,
            "deployed_model": self.deployed_model_name,
            "available_models": sorted(self.models.keys()),
            "loaded_model_count": len(self.models),
            "startup_error": self.startup_error,
        }

    def models_info(self) -> dict[str, Any]:
        models_payload = []
        for model_name, file_name in MODEL_FILE_NAMES.items():
            artifact_path = self.models_dir / file_name
            models_payload.append(
                {
                    "name": model_name,
                    "file_name": file_name,
                    "loaded": model_name in self.models,
                    "size_bytes": artifact_path.stat().st_size if artifact_path.exists() else 0,
                    "path": str(artifact_path),
                }
            )

        return {
            "models": models_payload,
            "models_dir": str(self.models_dir),
        }

    def stats(self) -> dict[str, Any]:
        if not self.training_summary:
            raise ApiError("Training statistics are unavailable because no model artifacts were loaded.", 503)
        return self.training_summary

    def predict(self, payload: dict[str, Any]) -> PredictionResult:
        if not self.ready or not self.deployed_model_name:
            raise ApiError(
                "Model service is not ready. Ensure the LIAR dataset files are present and the models can be trained.",
                503,
            )

        validated_payload = self._validate_payload(payload)
        artifact = self.models[self.deployed_model_name]
        feature_bundle = self._transform_payload(validated_payload, artifact)

        probabilities = artifact["model"].predict_proba(feature_bundle["full_matrix"])[0]
        predicted_index = int(np.argmax(probabilities))
        prediction = "REAL" if predicted_index == 1 else "FAKE"
        confidence = float(probabilities[predicted_index])

        explanation = {
            "top_tfidf_features": self._explain_text_features(
                artifact,
                feature_bundle["text_matrix"],
                predicted_index,
            ),
            "explanation_method": (
                "importance_weighted_tfidf"
                if artifact["model_name"] == "RandomForest"
                else "class_weighted_tfidf"
            ),
            "credibility_score": feature_bundle["credibility_score"] if validated_payload["speaker_provided"] else None,
            "text_statistics": feature_bundle["text_statistics"],
        }

        return PredictionResult(
            prediction_id=uuid.uuid4().hex,
            prediction=prediction,
            confidence=confidence,
            model=self.deployed_model_name,
            explanation=explanation,
        )

    @staticmethod
    def _validate_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ApiError("Request body must be a JSON object.", 400)

        raw_text = payload.get("text", "")
        text = str(raw_text).strip() if raw_text is not None else ""
        if not text:
            raise ApiError("Text cannot be empty", 400)
        if len(text) < MIN_INPUT_TEXT_LENGTH:
            raise ApiError("Please enter a longer statement", 400)
        if len(text) > MAX_INPUT_TEXT_LENGTH:
            text = text[:MAX_INPUT_TEXT_LENGTH]

        raw_speaker = payload.get("speaker")
        raw_party = payload.get("party")
        raw_subject = payload.get("subject")

        speaker = normalize_string(raw_speaker, default="unknown")
        party = normalize_string(raw_party, default="unknown")
        subject = normalize_string(raw_subject, default="unknown")

        return {
            "text": text,
            "speaker": speaker,
            "party": party,
            "subject": subject,
            "speaker_provided": bool(str(raw_speaker).strip()) if raw_speaker is not None else False,
        }

    def _transform_payload(self, payload: dict[str, Any], artifact: dict[str, Any]) -> dict[str, Any]:
        inference_frame = pd.DataFrame(
            [
                {
                    "statement": payload["text"],
                    "speaker": payload["speaker"],
                    "party": payload["party"],
                    "subject": payload["subject"],
                }
            ]
        )

        text_matrix = artifact["tfidf_vectorizer"].transform(inference_frame["statement"])
        text_statistics = compute_text_statistics(payload["text"])
        credibility_score = float(
            artifact["speaker_scores"].get(
                normalize_string(payload["speaker"]),
                artifact["default_speaker_score"],
            )
        )

        if artifact["model_name"] == "RandomForest":
            numeric_matrix = build_numeric_feature_matrix(
                inference_frame,
                artifact["speaker_scores"],
                artifact["default_speaker_score"],
            )
            party_matrix = artifact["party_encoder"].transform(inference_frame[["party"]])
            subject_matrix = artifact["subject_vectorizer"].transform(inference_frame["subject"])
            full_matrix = combine_engineered_features(text_matrix, numeric_matrix, party_matrix, subject_matrix)
        else:
            full_matrix = text_matrix

        return {
            "full_matrix": full_matrix,
            "text_matrix": text_matrix,
            "text_statistics": text_statistics,
            "credibility_score": round(credibility_score, 4),
        }

    @staticmethod
    def _explain_text_features(
        artifact: dict[str, Any],
        text_matrix: sparse.csr_matrix,
        predicted_index: int,
    ) -> list[dict[str, float | str]]:
        active_indices = text_matrix.indices
        if len(active_indices) == 0:
            return []

        text_feature_names = artifact["text_feature_names"]
        active_values = text_matrix.data

        if artifact["model_name"] in {"LogisticRegression", "NaiveBayes"}:
            coefficients = (
                artifact["model"].coef_[0]
                if artifact["model_name"] == "LogisticRegression"
                else artifact["model"].feature_log_prob_[1] - artifact["model"].feature_log_prob_[0]
            )
            direction = 1.0 if predicted_index == 1 else -1.0
            contributions = active_values * coefficients[active_indices] * direction
        else:
            # Random forest does not expose exact local feature contributions without extra dependencies,
            # so this explanation uses global feature importance weighted by the sample's active TF-IDF values.
            feature_importances = artifact["model"].feature_importances_[: len(text_feature_names)]
            contributions = active_values * feature_importances[active_indices]

        top_positions = np.argsort(contributions)[::-1][:5]
        top_features: list[dict[str, float | str]] = []
        for position in top_positions:
            contribution = float(contributions[position])
            if contribution <= 0:
                continue
            feature_index = int(active_indices[position])
            top_features.append(
                {
                    "feature": text_feature_names[feature_index],
                    "contribution": round(contribution, 4),
                }
            )
        return top_features
