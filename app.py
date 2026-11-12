from postgres_repository import PostgresRepository
from service import SubscriptionService

class Application:
    def __init__(self, dsn: str | None = None):
        """Создаёт зависимости. Всегда Postgres."""
        self.repo = PostgresRepository(dsn)
        self.service = SubscriptionService(self.repo)
