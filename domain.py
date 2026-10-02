from typing import Protocol


class Student:
    """Это Ученик"""

    def __init__(self, name: str, id:int | None = None):
        self.id = id
        self.name = name

    def __repr__(self):
        return str(self.name)


class Subscription:
    """Это абонeмент"""

    def __init__(self, owner: Student, total_visits: int = 0, id:int | None = None):
        self.id = id
        self.owner: Student = owner
        self.total_visits: int = total_visits

    def payment(self):
        """Алгоритм списания"""
        if self.total_visits > 0:
            self.total_visits -= 1
            return f"{self.owner} занятие списалось"
        else:
            return f"{self.owner} занятия закончились"

    def __repr__(self):
        return f"Владелец: {self.owner} Посещений осталось: {self.total_visits}"


class StorageRepository(Protocol):
    def init_db(self):
        """Инициализировать базу данных"""

    def insert_student(self, name: str):
        """Добавить ученика"""

    def insert_subscription(self, student_id:int, total_visits:int):
        """Добавить подписку"""

    def get_student_by_name(self, name:str):
        """Получить ученика по имени"""

    def get_subscription_by_student_name(self, name:str):
        """Получить подписку по имени ученика"""

    def update_subscription_visits(self, sub_id: int, total_visits: int):
        """Обновить количество подписок"""

    def get_all_students(self):
        """Все ученики из БД"""

    def get_all_subscriptions(self):
        """Все подписки"""

    def delete_subscription_student(self, student_id:int):
        """Удалить подписку у ученика"""

    def delete_student(self, student_id:int):
        """Удалить ученика"""
