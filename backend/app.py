from __future__ import annotations

import json
import logging
from typing import Any

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import config
from model_service import ApiError, FakeNewsDetectionService


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
)


def _configure_prediction_logger() -> logging.Logger:
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("prediction_audit")
    logger.setLevel(getattr(logging, config.LOG_LEVEL, logging.INFO))

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    file_handler = logging.FileHandler(config.PREDICTIONS_LOG_PATH, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger


def _append_feedback(payload: dict[str, Any]) -> None:
    feedback_entries: list[dict[str, Any]]
    config.FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    if config.FEEDBACK_PATH.exists():
        try:
            feedback_entries = json.loads(config.FEEDBACK_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            feedback_entries = []
    else:
        feedback_entries = []

    feedback_entries.append(payload)
    config.FEEDBACK_PATH.write_text(json.dumps(feedback_entries, indent=2), encoding="utf-8")


def create_app(service_override: FakeNewsDetectionService | None = None) -> Flask:
    app = Flask(__name__)
    app.config["MODEL_SERVICE"] = service_override or FakeNewsDetectionService()
    app.config["JSON_SORT_KEYS"] = False

    CORS(app, resources={r"/api/*": {"origins": config.API_ALLOWED_ORIGINS}})
    limiter.init_app(app)
    prediction_logger = _configure_prediction_logger()

    def current_service() -> FakeNewsDetectionService:
        return app.config["MODEL_SERVICE"]

    @app.get("/api/health")
    def health_check():
        return jsonify(current_service().health())

    @app.get("/api/stats")
    def model_stats():
        return jsonify(current_service().stats())

    @app.get("/api/models")
    def model_inventory():
        return jsonify(current_service().models_info())

    @app.post("/api/predict")
    @limiter.limit("30 per minute")
    def predict():
        payload = request.get_json(silent=True)
        prediction = current_service().predict(payload)
        request_text = payload.get("text", "") if isinstance(payload, dict) else ""
        prediction_logger.info(
            "prediction_id=%s ip=%s input_length=%s prediction=%s confidence=%.4f model=%s",
            prediction.prediction_id,
            request.remote_addr,
            len(str(request_text)),
            prediction.prediction,
            prediction.confidence,
            prediction.model,
        )
        return jsonify(prediction.to_dict())

    @app.post("/api/feedback")
    @limiter.limit("30 per minute")
    def submit_feedback():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            raise ApiError("Request body must be a JSON object.", 400)

        prediction_id = str(payload.get("prediction_id", "")).strip()
        correct = payload.get("correct")

        if not prediction_id:
            raise ApiError("prediction_id is required", 400)
        if not isinstance(correct, bool):
            raise ApiError("correct must be a boolean", 400)

        feedback_record = {
            "prediction_id": prediction_id,
            "correct": correct,
        }
        _append_feedback(feedback_record)
        return jsonify({"status": "saved", "feedback": feedback_record}), 201

    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        return jsonify({"error": error.message}), error.status_code

    @app.errorhandler(429)
    def handle_rate_limit(error):
        return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        app.logger.exception("Unexpected error while handling request")
        return jsonify({"error": "An unexpected server error occurred."}), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.FLASK_PORT, debug=config.IS_DEVELOPMENT)
