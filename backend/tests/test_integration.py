from __future__ import annotations

import time

import pytest
import requests


BASE_URL = "http://127.0.0.1:5000"
TEST_RESULTS = {"passed": 0, "total": 7}


@pytest.fixture(scope="session", autouse=True)
def session_summary():
    yield
    print(f"PASSED {TEST_RESULTS['passed']}/{TEST_RESULTS['total']} tests")


@pytest.fixture(scope="session")
def live_server():
    last_error: requests.RequestException | None = None
    for _ in range(10):
        try:
            response = requests.get(f"{BASE_URL}/api/health", timeout=3)
            response.raise_for_status()
            return BASE_URL
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(1)

    pytest.skip(f"Flask server is not running on {BASE_URL}: {last_error}")


def _mark_passed() -> None:
    TEST_RESULTS["passed"] += 1


def _assert_prediction_shape(payload: dict) -> None:
    assert payload["prediction"] in {"REAL", "FAKE"}
    assert isinstance(payload["confidence"], float)
    assert "model" in payload
    assert "prediction_id" in payload
    assert "explanation" in payload


def test_health_check_returns_ok(live_server):
    response = requests.get(f"{live_server}/api/health", timeout=3)

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    _mark_passed()


def test_stats_endpoint_returns_accuracy_over_threshold(live_server):
    response = requests.get(f"{live_server}/api/stats", timeout=5)
    payload = response.json()

    assert response.status_code == 200
    for model_name in ("LogisticRegression", "NaiveBayes", "RandomForest"):
        assert payload["models"][model_name]["test"]["accuracy"] > 0.5
    _mark_passed()


def test_predict_fake_statement_returns_valid_structure(live_server):
    response = requests.post(
        f"{live_server}/api/predict",
        json={
            "text": "This viral post says the city banned all private vehicles next week.",
            "speaker": "social media post",
            "party": "unknown",
        },
        timeout=5,
    )

    assert response.status_code == 200
    _assert_prediction_shape(response.json())
    _mark_passed()


def test_predict_real_statement_returns_valid_structure(live_server):
    response = requests.post(
        f"{live_server}/api/predict",
        json={
            "text": "The budget office reported that tax receipts increased compared with the previous fiscal year.",
            "speaker": "budget office",
            "party": "nonpartisan",
        },
        timeout=5,
    )

    assert response.status_code == 200
    _assert_prediction_shape(response.json())
    _mark_passed()


def test_empty_text_returns_400(live_server):
    response = requests.post(
        f"{live_server}/api/predict",
        json={"text": "", "speaker": "campaign", "party": "democrat"},
        timeout=5,
    )

    assert response.status_code == 400
    assert response.json()["error"] == "Text cannot be empty"
    _mark_passed()


def test_missing_optional_fields_returns_200(live_server):
    response = requests.post(
        f"{live_server}/api/predict",
        json={"text": "The report says inflation slowed in the fourth quarter."},
        timeout=5,
    )

    assert response.status_code == 200
    _assert_prediction_shape(response.json())
    _mark_passed()


def test_prediction_response_time_under_three_seconds(live_server):
    start_time = time.perf_counter()
    response = requests.post(
        f"{live_server}/api/predict",
        json={"text": "The labor market data showed improvement according to the official release."},
        timeout=5,
    )
    elapsed = time.perf_counter() - start_time

    assert response.status_code == 200
    assert elapsed < 3.0
    _mark_passed()
