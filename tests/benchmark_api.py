import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

def test_bench_students_endpoint(benchmark, client):
    def call():
        response = client.get("/students")
        assert response.status_code == 200
    benchmark(call)