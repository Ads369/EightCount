from domain import Student, Subscription

from storage import (
    insert_student,
    get_student_by_name,
    insert_subscription,
    get_all_subscriptions,
    get_subscription_by_student_name,
    update_subscription_visits,
    delete_subscription_student,
    delete_student,
    get_all_students,
)

def add_student(name:str):
    """Добавляет ученика"""
    student_id = insert_student(name)
    return f"Пользователь {name} добавлен, id={student_id}"

def add_subscription(owner:str, count_lession:int):
    """Добавляет подписку"""
    student= get_student_by_name(owner)
    if student is None:
        return f'Пользователь {owner} не найден'
    sub_id = insert_subscription(student.id, count_lession)
    return f'Подписка для {owner} создана, id={sub_id}'

def check_in(owner:str):
    """Проверка"""
    sub = get_subscription_by_student_name(owner)
    if sub is None:
        return f'Подписка для {owner} не найдена'
    result = sub.payment()
    update_subscription_visits(sub.id, sub.total_visits)
    return result

def remove_student_with_sub(name:str):
    """Удаляет студента с подпиской"""
    student = get_student_by_name(name)
    if student is None:
        return f'Пользователь {name} не найден'
    delete_subscription_student(student.id)
    delete_student(student.id)
    return f'Пользователь {name} удалён со всеми подписками'


def print_students():
    """Выводит пользователей"""
    print("\n Пользователи:")
    for s in get_all_students():
        print(f"  id={s.id}, name={s.name}")

def print_subscriptions():
    """Выводит подписки пользователей"""
    print("\n Подписки:")
    for sub in get_all_subscriptions():
        print(f"id={sub.id}, owner={sub.owner.name}, "
              f"total_visits={sub.total_visits}")

def demo():
    """Проверка"""
    # print(add_student("Алексей"))
    # print(add_subscription("Алексей",2))
    # print(check_in("Алексей"))
    # print_students()
    # print_subscriptions()
    # print(remove_student_with_sub("Алексей"))