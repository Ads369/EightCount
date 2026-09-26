from datetime import datetime


class Student:
    """Это Ученик"""
    def __init__(self, name:str):
        self.name = name

    def __repr__(self):
        return(str(self.name))


class Subscription:
    """Это абонeмент"""
    def __init__(self, owner: Student, count_lession: int = 0):
        self.owner: Student = owner
        self.total_visits: int = count_lession

    def payment(self):
        """Алгоритм списания"""
        if self.total_visits > 0:
            self.total_visits -= 1
            return f"{self.owner} занятие списалось"
        else:
            return f"{self.owner} занятия закончились"

    def __repr__(self):
        return(f"Владелец: {self.owner} Посещений осталось: {self.total_visits}")
