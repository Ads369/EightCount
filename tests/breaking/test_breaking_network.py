import httpx
import subprocess
import time
import pytest

def test_api_returns_503_when_db_is_down():
    subprocess.run(["docker", "compose", "stop", "postgres"])
    time.sleep(2)

    try:
        with httpx.Client(base_url="http://localhost:8000", timeout=2.0) as client:
            response = client.get("/students")
            assert response.status_code in [500, 503], f"Ожидали ошибку, получили {response.status_code}"
    
    finally:
        subprocess.run(["docker", "compose", "start", "postgres"])
        time.sleep(5)