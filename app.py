from sql_repository import SqliteRepository
from service import SubscriptionService


class Application:
    def __init__(self, db_path: str = "EightCount.db"):
        """Создаёт зависимости"""
        self.repo = SqliteRepository(db_path)
        self.service = SubscriptionService(self.repo)
