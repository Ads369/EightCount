from sql_repository import SqliteRepository
from service import SubscriptionService
from exceptions import DomainError



class Application:
    def __init__(self, db_path: str = "EightCount.db"):
        """Создаёт зависимости"""
        self.repo = SqliteRepository(db_path)
        self.service = SubscriptionService(self.repo)

    def run(self) -> None:
        """Запускает сценарий."""
        try:
            self.service.check_in("Алексей")
        except DomainError as e:
            print(f"Ошибка: {e}")
