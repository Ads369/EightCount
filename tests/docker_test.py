# import httpx
# import pytest

# BASE_URL = "http:localhost:8000"

# def test_real_postgres_connection():
#     with httpx.Client(base_url=BASE_URL, timeout=5.0) as client:
#         response = client.post("/students", json={"name": "Test E2E", "owner": "Owner"})
#         assert response.status_code == 201, "Не удалось создать студента через docker"

#         student_id = response.json()["id"]

#         response_visit = client.post(f"/subscription/{student_id}/visits", json={"visits": 5})
#         assert response_visit.status_code == 200

#         response_get = client.get(f"/students/{student_id}")
#         assert response_get.status_code == 200
#         assert response_get.json()["name"] == "Test E2E"