import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.mark.parametrize("bad_payload", [
    {"student_id": "НЕ_ЧИСЛО", "visits": 1},
    {"student_id": 1, "visits": "МНОГО"},
    {"student_id": 1, "visits": -5},
    {"student_id": None, "visits": 1},
    {}
])
def test_api_rejects_bad_data_gracefully(bad_payload):
    response = client.post("/subscriptions", json=bad_payload)
    assert response.status_code in [400, 422], f"Сервер упал с 500! Ответ: {response.text}"