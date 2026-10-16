from domain import StorageRepository, Student
import logging
from exceptions import SubscriptionNotFoundError, NoLessionsLeftError, StudentNotFoundError,DbError, StudentAlreadyExistError

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
            logger.error(f"Такой ученик уже существует: {name}")
            raise StudentAlreadyExistError(f"Ученик {name} уже существует")
        student_id = self.repo.insert_student(name)
        logger.info(f'Добавлен: {name} id = {student_id}')

    def add_subscription(self, owner: str, total_visits: int):
        """Создаёт или пополняет подписку."""
        logger.info(f"Запрос на подписку: {owner}, visits={total_visits}")
        student = self.repo.get_student_by_name(owner)
        if student is None:
            logger.warning(f"Ученик {owner} не найден")
            raise StudentNotFoundError(f"Ученик {owner} не найден")
        sub_id = self.repo.add_visits_to_subscription(student.id, total_visits)
        logger.info(f"Подписка для {owner} обновлена, sub_id={sub_id}")

    def check_in(self, owner: str):
        """Проверка"""
        logger.info(f'Запрос на списание подписки: {owner}')
        
        student = self.repo.get_student_by_name(owner)
        if student is None:
            logger.error(f'Ученик {owner} не найден ')
            raise StudentNotFoundError(f'Ученик {owner} не найден')
        
        sub = self.repo.get_subscription_by_student_name(owner)
        if sub is None:
            logger.error(f"Подписка не найдена: {owner}")
            raise SubscriptionNotFoundError(f"Подписка для {owner} не найдена")
        
        if sub.total_visits <= 0:
            logger.error(f'Занятия закончились: {owner}')
            raise NoLessionsLeftError(f'У {owner} закончились занятия')
        
        result = sub.payment()
        self.repo.update_subscription_visits(sub.id, sub.total_visits)

        logger.info(f'Списание прошло успешно: {owner}, осталось подписок = {sub.total_visits}')
        return result
    
    def get_all_students(self):
        """Список учеников"""
        return self.repo.get_all_students()

    def remove_subscription(self, owner: str):
        """Удаляет подписку ученика. Ученик остаётся."""
        logger.info(f"Запрос на удаление подписки: {owner}")

        student = self.repo.get_student_by_name(owner)
        if student is None:
            logger.warning(f"Ученик {owner} не найден")
            raise StudentNotFoundError(f"Ученик {owner} не найден")

        sub = self.repo.get_subscription_by_student_name(owner)
        if sub is None:
            logger.warning(f"Подписка для {owner} не найдена")
            raise SubscriptionNotFoundError(f"Подписка для {owner} не найдена")

        self.repo.delete_subscriptions_by_student(student.id)
        logger.info(f"Подписка для {owner} удалена")
        return f"Подписка для {owner} удалена"

    def remove_student_with_sub(self, name: str):
        """Удаляет ученика и его подписку."""
        logger.info(f"Запрос на удаление ученика: {name}")

        student = self.repo.get_student_by_name(name)
        if student is None:
            logger.warning(f"Ученик {name} не найден")
            raise StudentNotFoundError(f"Ученик {name} не найден")

        self.repo.delete_subscriptions_by_student(student.id)
        logger.info(f"Ученик {name} удалён со всеми подписками")
        return f"Ученик {name} удалён со всеми подписками"

