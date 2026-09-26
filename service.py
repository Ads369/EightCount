from domain import Student, Subscription
from storage import students, subscriptions


def add_student(name:str):
    """Добавляет ученика"""
    key = len(students)
    students[key]= Student(name)

def add_subscription(owner:str, count_lession:int):
    """Добавляет подписку"""
    for student in students.values():
        if student.name == owner:
            break
    else:
        return f"Ученик {owner} не найден"
    key = len(subscriptions)
    subscriptions[key]= Subscription(student, count_lession)


def check_in(owner:str):
    """Проверка"""
    for sub in subscriptions.values():
        if sub.owner.name == owner:
            break
    else:
        return f" Подписка у {owner} не найдена"
    return sub.payment()
