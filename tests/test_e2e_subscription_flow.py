import uuid

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

OWNER = f"E2E Student {uuid.uuid4().hex[:8]}"


def test_full_student_subscription_checkin_flow():
    """E2E-тест"""
    r = client.post("/students", json={"name": OWNER})
    assert r.status_code == 200, r.text
    _, student_id = r.json()["status"]

    r = client.post(
        "/subscriptions", json={"owner": OWNER, "total_visits": 3}
    )
    assert r.status_code == 200, r.text

    for _ in range(3):
        r = client.post("/check-in", json={"owner": OWNER})
        assert r.status_code == 200, r.text

    r = client.post("/check-in", json={"owner": OWNER})
    assert r.status_code == 404, r.text

    r = client.get("/subscriptions")
    assert r.status_code == 200
    subs = r.json()
    target = [s for s in subs if s["owner"] == OWNER][0]
    assert target["total_visits"] == 0
