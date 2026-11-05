from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from exceptions import StudentNotFoundError, SubscriptionNotFoundError, DbError, StudentAlreadyExistError

client = TestClient(app)


@patch("routes.service")
def test_delete_student_db_error_returns_500(mock_service):
    mock_service.remove_student.side_effect = DbError("Ошибка БД")

    response = client.delete("/students/Ivan")

    assert response.status_code == 500


@patch("routes.service")
def test_delete_subscription_not_found_returns_404(mock_service):
    mock_service.remove_subscription.side_effect = SubscriptionNotFoundError("Подписка не найдена")

    response = client.delete("/subscription/Nonexistent")

    assert response.status_code == 404


@patch("routes.service")
def test_delete_subscription_db_error_returns_404(mock_service):
    mock_service.remove_subscription.side_effect = DbError("Ошибка БД")

    response = client.delete("/subscription/Ivan")

    assert response.status_code == 404


@patch("routes.service")
def test_check_in_domain_error_returns_404(mock_service):
    mock_service.check_in.side_effect = SubscriptionNotFoundError("Подписка не найдена")

    response = client.post("/check-in", json={"owner": "Ivan"})

    assert response.status_code == 404


@patch("routes.service")
def test_delete_student_not_found_returns_400(mock_service):
    mock_service.remove_student.side_effect = StudentNotFoundError("Ученик не найден")

    response = client.delete("/students/Nonexistent")

    assert response.status_code == 400


@patch("routes.service")
def test_create_student_already_exists_returns_409(mock_service):
    mock_service.add_student.side_effect = StudentAlreadyExistError("Уже существует")

    response = client.post("/students", json={"name": "Ivan"})

    assert response.status_code == 409


@patch("routes.service")
def test_create_student_db_error_returns_500(mock_service):
    mock_service.add_student.side_effect = DbError("Ошибка БД")

    response = client.post("/students", json={"name": "Ivan"})

    assert response.status_code == 500
