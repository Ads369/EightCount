from pydantic import ValidationError
from models import AddStudentRequest, AddSubscriptionRequest
from exceptions import ValidationError as MyValidationError


def validate_add_student(name):
    """Валидирует add_student"""
    try:
        return AddStudentRequest(name=name)
    except ValidationError as e:
        raise MyValidationError(f"Некорректные данные {e}")
 

def validate_add_subscription(owner, total_visits):
    """"Валидирует add_subscription"""
    try:
        return AddSubscriptionRequest(owner=owner, total_visits=total_visits)
    except ValidationError as e:
        raise MyValidationError(f"Некорректные данные для добавления подписки {e}")
