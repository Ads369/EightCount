import os
import socket
import subprocess
import time

import pytest


def _port_open(host="127.0.0.1", port=8000, timeout=0.5):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


@pytest.fixture(scope="session", autouse=True)
def uvicorn_server():
    """Поднимает uvicorn на 8000 для системных тестов, если порт свободен."""
    if _port_open():
        yield
        return

    env = os.environ.copy()
    env.setdefault("DB_BACKEND", "postgres")
    env.setdefault("DATABASE_URL", "postgresql://appuser:apppassword@localhost:5432/appdb")

    proc = subprocess.Popen(
        ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        env=env,
        cwd=os.path.dirname(os.path.abspath(__file__)),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        for _ in range(40):
            if _port_open():
                break
            time.sleep(0.25)
        yield
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
