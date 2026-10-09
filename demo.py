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

def test(func, *args):
    try:
        print(f"{func(*args)}")
    except DomainError as e:
        print(f"{type(e).__name__}: {e}")
    except DbError as e:
        print(f"DbError: {e}")

def main():
    if os.path.exists("demo_test.db"):
        os.remove("demo_test.db")

    service = Application("demo_test.db").service

    os.chmod("demo_test.db", stat.S_IREAD)

    test(service.add_student,"Алексей")
    test(service.add_subscription,"Алексей",2)
    test(service.check_in,"Алексей")
    test(service.check_in,"Алексей")
    test(service.check_in,"Алексей")

if __name__ == "__main__":
    main()
    logging.info("all good")