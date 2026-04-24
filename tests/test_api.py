from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture()
def client(monkeypatch):
    model_service_module = importlib.import_module("model_service")
    app_module = importlib.import_module("app")
    saved_feedback: list[dict[str, object]] = []

    monkeypatch.setattr(app_module, "_configure_prediction_logger", lambda: app_module.logging.getLogger("test_logger"))
    monkeypatch.setattr(app_module, "_append_feedback", lambda payload: saved_feedback.append(payload))

    class FakeService:
        def health(self):
            return {
                "status": "ok",
                "deployed_model": "RandomForest",
                "available_models": ["LogisticRegression", "NaiveBayes", "RandomForest"],
                "loaded_model_count": 3,
                "startup_error": None,
            }

        def stats(self):
            return {
                "deployed_model": "RandomForest",
                "models": {},
            }

        def models_info(self):
            return {
                "models": [
                    {
                        "name": "RandomForest",
                        "file_name": "random_forest.pkl",
                        "loaded": True,
                        "size_bytes": 1024,
                        "path": "backend/models/random_forest.pkl",
                    }
                ],
                "models_dir": "backend/models",
            }

        def predict(self, payload):
            validated = model_service_module.FakeNewsDetectionService._validate_payload(payload)
            return model_service_module.PredictionResult(
                prediction_id="pred-123",
                prediction="REAL" if "true" in validated["text"].lower() else "FAKE",
                confidence=0.87,
                model="RandomForest",
                explanation={
                    "top_tfidf_features": [
                        {"feature": "claim", "contribution": 0.1234},
                    ],
                    "explanation_method": "importance_weighted_tfidf",
                    "credibility_score": 0.61 if validated["speaker_provided"] else None,
                    "text_statistics": {
                        "text_length": float(len(validated["text"])),
                        "punctuation_count": 0.0,
                        "all_caps_ratio": 0.0,
                        "exclamation_count": 0.0,
                    },
                },
            )

    test_app = app_module.create_app(service_override=FakeService())
    test_app.config["TESTING"] = True
    test_app.config["SAVED_FEEDBACK"] = saved_feedback

    with test_app.test_client() as test_client:
        yield test_client


def test_health_returns_200(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"


def test_models_route_returns_loaded_models(client):
    response = client.get("/api/models")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["models"][0]["loaded"] is True
    assert payload["models"][0]["size_bytes"] == 1024


def test_predict_with_valid_input_returns_prediction(client):
    response = client.post(
        "/api/predict",
        json={
            "text": "This statement is true according to the report.",
            "speaker": "campaign spokesperson",
            "party": "democrat",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["prediction"] in {"REAL", "FAKE"}
    assert "confidence" in payload
    assert payload["model"] == "RandomForest"
    assert payload["prediction_id"] == "pred-123"


def test_predict_with_short_text_returns_400(client):
    response = client.post(
        "/api/predict",
        json={
            "text": "too short",
            "speaker": "campaign spokesperson",
            "party": "democrat",
        },
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["error"] == "Please enter a longer statement"


def test_predict_with_empty_text_returns_400(client):
    response = client.post(
        "/api/predict",
        json={
            "text": "",
            "speaker": "campaign spokesperson",
            "party": "democrat",
        },
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["error"] == "Text cannot be empty"


def test_predict_with_long_text_is_truncated_and_returns_prediction(client):
    response = client.post(
        "/api/predict",
        json={
            "text": "reported claim " * 500,
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["prediction"] in {"REAL", "FAKE"}
    assert payload["explanation"]["text_statistics"]["text_length"] == 5000.0


def test_feedback_endpoint_persists_boolean_feedback(client):
    response = client.post(
        "/api/feedback",
        json={
            "prediction_id": "pred-123",
            "correct": True,
        },
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["status"] == "saved"
    assert payload["feedback"]["correct"] is True
