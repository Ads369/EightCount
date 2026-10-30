import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.mark.parametrize("bad_payload", [
{"owner": "Ivan", "total_visits": "МНОГО"},
    {"owner": "", "total_visits": 1},
    {"owner": "Ivan", "total_visits": -5},
    {"owner": None, "total_visits": 1},
    {}
])
def test_api_rejects_bad_data_gracefully(bad_payload):
    response = client.post("/subscriptions", json=bad_payload)
    assert response.status_code in [400, 422], f"Сервер упал с 500! Ответ: {response.text}"