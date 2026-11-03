from unittest.mock import MagicMock

from service import SubscriptionService
from domain import Student, Subscription
from exceptions import (
    StudentNotFoundError,
    SubscriptionNotFoundError,
    NoLessionsLeftError,
    StudentAlreadyExistError,
)


def test_check_in_raises_no_lessions_when_balance_is_zero():
    """Функциональный тест бизнес-логики сервиса"""
    repo = MagicMock()
    repo.get_student_by_name.return_value = Student(id=1, name="Ivan")
    repo.get_subscription_by_student_name.return_value = Subscription(
        owner=Student(id=1, name="Ivan"), total_visits=0, id=10
    )
    repo.try_spend_visit.return_value = None

    service = SubscriptionService(repo)

    try:
        service.check_in("Ivan")
        assert False, "Ожидалось NoLessionsLeftError"
    except NoLessionsLeftError as e:
        assert "Ivan" in str(e)


def test_check_in_returns_remaining_visits():
    repo = MagicMock()
    repo.get_student_by_name.return_value = Student(id=1, name="Ivan")
    repo.get_subscription_by_student_name.return_value = Subscription(
        owner=Student(id=1, name="Ivan"), total_visits=3, id=10
    )
    repo.try_spend_visit.return_value = 2

    service = SubscriptionService(repo)
    result = service.check_in("Ivan")

    assert result == 2


def test_add_student_raises_when_already_exists():
    repo = MagicMock()
    repo.get_student_by_name.return_value = Student(id=1, name="Ivan")

    service = SubscriptionService(repo)

    try:
        service.add_student("Ivan")
        assert False, "Ожидалось StudentAlreadyExistError"
    except StudentAlreadyExistError:
        pass


def test_add_subscription_raises_when_student_not_found():
    repo = MagicMock()
    repo.get_student_by_name.return_value = None

    service = SubscriptionService(repo)

    try:
        service.add_subscription("Unknown", 5)
        assert False, "Ожидалось StudentNotFoundError"
    except StudentNotFoundError:
        pass
