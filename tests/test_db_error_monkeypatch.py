import psycopg2
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from main import app
from postgres_repository import PostgresRepository
from exceptions import DbError

client = TestClient(app)


def _boom_connect(*args, **kwargs):
    """Подмена psycopg2.connect, которая всегда выбрасывает OperationalError."""
    raise psycopg2.OperationalError("БД временно недоступна")


def test_repo_get_connection_raises_db_error(monkeypatch):
    """Если psycopg2.connect падает — _get_connection бросает DbError."""
    monkeypatch.setattr("psycopg2.connect", _boom_connect)

    repo = PostgresRepository.__new__(PostgresRepository)
    repo.dsn = "postgresql://user:pass@localhost:5432/db"

    try:
        repo._get_connection()
        assert False, "Ожидался DbError"
    except DbError:
        pass


def test_repo_init_db_raises_db_error(monkeypatch):
    """Если init_db не может подключиться — бросает DbError."""
    monkeypatch.setattr("psycopg2.connect", _boom_connect)

    repo = PostgresRepository.__new__(PostgresRepository)
    repo.dsn = "postgresql://user:pass@localhost:5432/db"

    try:
        repo.init_db()
        assert False, "Ожидался DbError"
    except DbError:
        pass


def test_repo_get_student_by_name_raises_db_error(monkeypatch):
    """Если запрос к БД падает — get_student_by_name бросает DbError."""
    monkeypatch.setattr("psycopg2.connect", _boom_connect)

    repo = PostgresRepository.__new__(PostgresRepository)
    repo.dsn = "postgresql://user:pass@localhost:5432/db"

    try:
        repo.get_student_by_name("Иван")
        assert False, "Ожидался DbError"
    except DbError:
        pass


def test_repo_try_spend_visit_raises_db_error(monkeypatch):
    """Если UPDATE падает — try_spend_visit бросает DbError."""
    monkeypatch.setattr("psycopg2.connect", _boom_connect)

    repo = PostgresRepository.__new__(PostgresRepository)
    repo.dsn = "postgresql://user:pass@localhost:5432/db"

    try:
        repo.try_spend_visit(1)
        assert False, "Ожидался DbError"
    except DbError:
        pass


def test_route_show_students_returns_503_when_db_down(monkeypatch):
    """GET /students возвращает 503, если service.get_all_students бросает psycopg2.OperationalError."""
    import routes
    import psycopg2 as psycopg2_module

    from routes import service

    # routes.py не импортирует psycopg2, поэтому except psycopg2.OperationalError
    # вызывает NameError. Добавляем имя в модуль routes, чтобы except сработал.
    monkeypatch.setattr(routes, "psycopg2", psycopg2_module, raising=False)

    original = service.get_all_students

    def boom(*args, **kwargs):
        raise psycopg2_module.OperationalError("БД недоступна")

    monkeypatch.setattr(service, "get_all_students", boom)

    try:
        response = client.get("/students")
        assert response.status_code == 503, f"Ожидали 503, получили {response.status_code}"
    finally:
        monkeypatch.undo()


def test_route_create_student_returns_500_on_db_error(monkeypatch):
    """POST /students возвращает 500, если service.add_student бросает DbError."""
    from routes import service
    from exceptions import DbError

    original = service.add_student

    def boom(*args, **kwargs):
        raise DbError("Ошибка БД")

    monkeypatch.setattr(service, "add_student", boom)

    try:
        response = client.post("/students", json={"name": "Иван"})
        assert response.status_code == 500, f"Ожидали 500, получили {response.status_code}"
    finally:
        monkeypatch.undo()


def test_route_check_in_returns_500_on_db_error(monkeypatch):
    """POST /check-in возвращает 500, если service.check_in бросает DbError."""
    from routes import service
    from exceptions import DbError

    original = service.check_in

    def boom(*args, **kwargs):
        raise DbError("Ошибка БД")

    monkeypatch.setattr(service, "check_in", boom)

    try:
        response = client.post("/check-in", json={"owner": "Иван"})
        assert response.status_code == 500, f"Ожидали 500, получили {response.status_code}"
    finally:
        monkeypatch.undo()
