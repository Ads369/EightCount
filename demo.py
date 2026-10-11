import os
import logging
import stat


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)

from app import Application
from exceptions import DomainError, DbError                                                                  
from pydantic import ValidationError
from validators import validate_add_student, validate_add_subscription



def test(func, *args):
    """Тест на выявление проблем"""
    try:
        func(*args)
    except DomainError as e:
        print(f"{type(e).__name__}: {e}")
    except DbError as e:
        print(f"DbError: {e}")
    except ValidationError as e:
        print(f"ValidationError: {e}")

def validated_add_student(service, name):
    """Валидирует и вызывает add_student"""
    req = validate_add_student(name)
    return service.add_student(req.name)

def validated_add_subscription(service, owner, total_visits):
    """Валидирует add_subscription"""
    req = validate_add_subscription(owner, total_visits)
    return service.add_subscription(req.owner, req.total_visits)

def main():
    """Создать БД, при повторном запуске удаляет старую"""
    if os.path.exists("demo_test.db"):
        os.remove("demo_test.db")

    """Создать БД readonly"""
    # os.chmod("demo_test.db", stat.S_IREAD)

    service = Application("demo_test.db").service

    test(validated_add_student,service, "Алексей")
    test(validated_add_subscription,service,"Алексей",2)
    test(service.check_in,"Алексей")

    """Запрос с ошибкой"""
    test(validated_add_student,service,"123123")
    test(validated_add_subscription,service,"123123","qwe")
    test(service.check_in,"123123")

if __name__ == "__main__":
    main()
    logging.info("all good")