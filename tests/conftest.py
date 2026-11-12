import os
import socket
import subprocess
import sys
import time

import psycopg2
import pytest


DEFAULT_DATABASE_URL = "postgresql://appuser:apppassword@localhost:5432/appdb"


def _database_url() -> str:
    """Единый DSN для тестов: тот же, что использует приложение."""
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


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
    env.setdefault("DATABASE_URL", _database_url())

    # sys.executable, а не "uvicorn": тесты запускаются из venv, где бинарник
    # может отсутствовать в PATH.
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
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


@pytest.fixture
def pg_cleanup():
    """Регистрирует тестовые student_id и имена для удаления из PostgreSQL после теста.

    Гарантирует, что интеграционные тесты не оставляют мусора в БД и не зависят
    друг от друга при параллельном или последовательном прогоне.
    """
    student_ids = []
    names = []

    def register(student_id=None, name=None):
        if student_id is not None:
            student_ids.append(student_id)
        if name is not None:
            names.append(name)

    yield register

    if not student_ids and not names:
        return

    conn = psycopg2.connect(_database_url(), connect_timeout=3)
    try:
        with conn:
            with conn.cursor() as cur:
                for sid in student_ids:
                    cur.execute("DELETE FROM subscriptions WHERE student_id = %s", (sid,))
                    cur.execute("DELETE FROM students WHERE id = %s", (sid,))
                for nm in names:
                    # Удаляем и по имени на случай, если тест создал строку
                    # через сервис/БД и id в фикстуре не совпал.
                    cur.execute(
                        "DELETE FROM subscriptions WHERE student_id IN "
                        "(SELECT id FROM students WHERE name = %s)",
                        (nm,),
                    )
                    cur.execute("DELETE FROM students WHERE name = %s", (nm,))
    finally:
        conn.close()
