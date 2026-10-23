from sql_repository import SqliteRepository
from postgres_repository import PostgresRepository
from service import SubscriptionService
import os

class Application:
    def __init__(self, dsn: str | None = None, use_postgres: bool | None = None):
        """Создаёт зависимости."""
        if use_postgres is None:
            use_postgres = os.environ.get("DB_BACKEND", "sqlite") == "postgres"

        if use_postgres:
            self.repo = PostgresRepository(dsn)
        else:
            self.repo = SqliteRepository("EightCount.db")
        self.service = SubscriptionService(self.repo)
