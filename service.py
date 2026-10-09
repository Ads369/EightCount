from domain import StorageRepository
import logging
from exceptions import SubscriptionNotFoundError, NoLessionsLeftError, StudentNotFoundError,DbError

logger = logging.getLogger(__name__)

class SubscriptionService:
    def __init__(self, repo: StorageRepository):
        self.repo = repo
        self.repo.init_db()

    def add_student(self, name: str):
        """Добавляет Студента"""
        logger.info(f'Запрос на добавление: {name}')
        existing = self.repo.get_student_by_name(name)
        if existing is not None:
            logger.warning("Ошибка в добавлении ученика")
        student_id = self.repo.insert_student(name)
        logger.info(f'Добавлен: {name}')
        return f"Пользователь {name} добавлен, id={student_id}"

    def add_subscription(self, owner: str, total_visits: int):
        """Добавляет подписку"""
        student = self.repo.get_student_by_name(owner)
        if student is None:
            return ""
        sub_id = self.repo.insert_subscription(student.id, total_visits)
        return f"Подписка для {owner} создана, id={sub_id}"

    def check_in(self, owner: str):
        """Проверка"""
        logger.info(f'Запрос на списание подписки: {owner}')
        
        student = self.repo.get_student_by_name(owner)
        if student is None:
            logger.warning(f'Ученик {owner} не найден ')
            raise StudentNotFoundError(f'Ученик {owner} не найден')
        
        sub = self.repo.get_subscription_by_student_name(owner)
        if sub is None:
            logger.warning(f"Подписка не найдена: {owner}")
            raise SubscriptionNotFoundError(f"Подписка для {owner} не найдена")
        
        if sub.total_visits <= 0:
            logger.warning(f'Занятия закончились: {owner}')
            raise NoLessionsLeftError(f'У {owner} закончились занятия')
        
        result = sub.payment()
        self.repo.update_subscription_visits(sub.id, sub.total_visits)

        logger.info(f'Списание прошло успешно: {owner}, осталось подписок = {sub.total_visits}')
        return result

    def remove_student_with_sub(self, name: str):
        """Удаляет студента с подпиской"""
        student = self.repo.get_student_by_name(name)
        if student is None:
            return f"Пользователь {name} не найден"
        self.repo.delete_subscription_student(student.id)
        self.repo.delete_student(student.id)
        return f"Пользователь {name} удалён со всеми подписками"

    def print_students(self):
        """Выводит пользователей"""
        print("\n Пользователи:")
        for s in self.repo.get_all_students():
            print(f"  id={s.id}, name={s.name}")

    def print_subscriptions(self):
        """Выводит подписки пользователей"""
        print("\n Подписки:")
        for sub in self.repo.get_all_subscriptions():
            print(f"id={sub.id}, owner={sub.owner.name},total_visits={sub.total_visits}")
