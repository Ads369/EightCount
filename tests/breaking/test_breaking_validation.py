import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch

client = TestClient(app)

@patch("postgres_repository.PostgresRepository.add_visits_to_subscription")
@pytest.mark.parametrize("bad_payload, expected_field, expected_error_type", [
    ({"owner": "Ivan", "total_visits": "МНОГО"}, "total_visits", "int_parsing"),
    ({"owner": "", "total_visits": 1}, "owner", "string_too_short"),
    ({"owner": "Ivan", "total_visits": -5}, "total_visits", "greater_than"),
    ({"owner": None, "total_visits": 1}, "owner", "string_type"),
    ({}, "owner", "missing"),
])

def test_api_rejects_bad_data_gracefully(mock_add_visits, bad_payload, expected_field, expected_error_type):
    response = client.post("/subscriptions", json=bad_payload)
    
    assert response.status_code == 422, f"Жду 422, получил {response.status_code}. Ответ: {response.text}"
    
    error_data = response.json()
    assert error_data["detail"][0]["loc"][-1] == expected_field, \
        f"Ожидали ошибку в поле '{expected_field}', а получили {error_data}"
    
    assert error_data["detail"][0]["type"] == expected_error_type
    
    mock_add_visits.assert_not_called()