from domain import StorageRepository, Student
import logging
import os
import time
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
        return name, student_id

    def add_subscription(self, owner: str, total_visits: int):
        """Создаёт или пополняет подписку."""
        logger.info(f"Запрос на подписку: {owner}, visits={total_visits}")
        student = self.repo.get_student_by_name(owner)
        if student is None:
            logger.warning(f"Ученик {owner} не найден")
            raise StudentNotFoundError(f"Ученик {owner} не найден")
        sub_id = self.repo.add_visits_to_subscription(student.id, total_visits)
        logger.info(f"Подписка для {owner} обновлена")
        return sub_id

    def check_in(self, owner: str):
        """Списание одного занятия (атомарно, защищено от гонки)."""
        logger.info(f'Запрос на списание подписки: {owner}')
        
        student = self.repo.get_student_by_name(owner)
        if student is None:
            logger.error(f'Ученик {owner} не найден ')
            raise StudentNotFoundError(f'Ученик {owner} не найден')
        
        sub = self.repo.get_subscription_by_student_name(owner)
        if sub is None:
            logger.error(f"Подписка не найдена: {owner}")
            raise SubscriptionNotFoundError(f"Подписка для {owner} не найдена")
        
        # ДЕМО: расширяем окно гонки между чтением и записью.
        # Даже с этим sleep атомарный UPDATE не даст списать дважды.
        delay = float(os.environ.get("CHECK_IN_DELAY", "0"))
        if delay:
            time.sleep(delay)

        remaining = self.repo.try_spend_visit(sub.id)
        if remaining is None:
            logger.error(f'Занятия закончились: {owner}')
            raise NoLessionsLeftError(f'У {owner} закончились занятия')

        logger.info(f'Списание прошло успешно: {owner}, осталось занятий = {remaining}')
        return remaining
    
    def get_all_subscription(self):
        """Подписки"""
        subs = self.repo.get_all_subscriptions()
        return [
            {
                "id": s.id,
                "owner": s.owner.name,
                "total_visits": s.total_visits
            }
            for s in subs
        ]
    
    def get_all_students(self):
        """Возвращает список учеников."""
        return self.repo.get_all_students()

    def remove_subscription(self, owner: str):
        """Удаляет подписку ученика. Ученик остаётся."""
        logger.warning(f"Запрос на удаление подписки {owner}")

        student = self.repo.get_student_by_name(owner)
        if student is None:
            logger.warning(f"Ученик {owner} не найден")
            raise StudentNotFoundError(f"Ученик {owner} не найден")

        sub = self.repo.get_subscription_by_student_name(owner)
        if sub is None:
            logger.error(f"Подписка для {owner} не найдена")
            raise SubscriptionNotFoundError(f"Подписка для {owner} не найдена")

        self.repo.delete_subscriptions_by_student(student.id)
        logger.info(f"Подписка для {owner} удалена")

    def remove_student(self, name: str):
        """Удаляет ученика"""
        logger.warning(f"Запрос на удаление пользователя {name}")

        student = self.repo.get_student_by_name(name)
        if student is None:
            logger.warning(f"Ученик {name} не найден")
            raise StudentNotFoundError(f"Ученик {name} не найден")

        self.repo.delete_student(student.id)
        logger.info(f"Пользователь {name} удалён")


