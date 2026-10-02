from sql_repository import SqliteRepository
from service import SubscriptionService

class Application:
    def __init__(self, db_path: str = "EightCount.db"):
        """Создаёт зависимости"""
        self.repo = SqliteRepository(db_path)
        self.repo.init_db()
        self.service = SubscriptionService(self.repo)

    def run(self):
        """Запускает сценарий"""
        self.service.add_student("Алексей")
        self.service.add_subscription("Алексей", 3)
        self.service.check_in("Алексей")
        self.service.print_students()
        self.service.print_subscriptions()
        self.service.remove_student_with_sub("Алексей")