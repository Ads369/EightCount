import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)

from app import Application
from exceptions import DomainError


def check(service, name):
    try:
        print(f"OK: {service.check_in(name)}")
    except DomainError as e:
        print(f"{type(e).__name__}: {e}")


def main():
    if os.path.exists("demo_test.db"):
        os.remove("demo_test.db")

    service = Application("demo_test.db").service

    service.add_student("Алексей")
    service.add_subscription("Алексей", 3)
    check(service, "Алексей")

    # service.add_student("Роман")
    # service.add_subscription("Роман", 1)
    # check(service, "Роман")
    # check(service, "Роман")

    # service.add_student("Иван")
    # check(service, "Иван")

    # service.add_student("Виктор")
    # check(service, "Виктор")


if __name__ == "__main__":
    main()
