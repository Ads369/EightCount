import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, Mock

"""ФУНКЦИОНАЛЬНЫЙ ТЕСТ"""

@patch("postgres_repository.PostgresRepository.add_visits_to_subscription")
def test_api_rejects_bad_data(mock_add_visits):
    client = TestClient(app)
    bad_payloads = [
        {"student_id": "НЕ ЧИСЛО", "visits": 1},
        {"student_id": 1, "visits": "МНОГА"},
        {"student_id": 1, "visits": -5},
        {"student_id": None, "visits": 1},
        {}
    ]

    for payload in bad_payloads:
        response = client.post("/subscriptions", json=payload)
        assert response.status_code == 422, f"Жду 422 а получил {response.status_code}. Ответ: {response.text}"

        mock_add_visits.assert_not_called()

@pytest.mark.parametrize("bad_payload", [
{"owner": "Ivan", "total_visits": "МНОГО"},
    {"owner": "", "total_visits": 1},
    {"owner": "Ivan", "total_visits": -5},
    {"owner": None, "total_visits": 1},
    {}
])
def test_api_rejects_bad_data_gracefully(bad_payload):
    client = TestClient(app)
    response = client.post("/subscriptions", json=bad_payload)
    assert response.status_code in [400, 422], f"Сервер упал с 500! Ответ: {response.text}"