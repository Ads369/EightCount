def validate_student_name(name):
    """Валидация имени ученика."""
    if not isinstance(name, str):
        raise ValueError("Имя должно быть строкой")
    if not name or not name.strip():
        raise ValueError("Имя не может быть пустым")
    if len(name) > 100:
        raise ValueError("Имя слишком длинное (макс. 100 символов)")
    return name.strip()


def validate_subscription_owner(owner):
    """Валидация владельца подписки."""
    if not isinstance(owner, str):
        raise ValueError("Владелец должен быть строкой")
    if not owner or not owner.strip():
        raise ValueError("Владелец не может быть пустым")
    if len(owner) > 200:
        raise ValueError("Владелец слишком длинный (макс. 200 символов)")
    return owner.strip()


def validate_total_visits(total_visits):
    """Валидация количества визитов."""
    if not isinstance(total_visits, int) or isinstance(total_visits, bool):
        raise ValueError("Количество визитов должно быть целым числом")
    if total_visits <= 0:
        raise ValueError("Количество визитов должно быть больше 0")
    if total_visits > 1000:
        raise ValueError("Количество визитов не может превышать 1000")
    return total_visits


def validate_check_in_owner(owner):
    """Валидация владельца для проверки (check-in)."""
    return validate_subscription_owner(owner)


def validate_delete_student_name(name):
    """Валидация имени для удаления ученика."""
    return validate_student_name(name)


def validate_delete_subscription_owner(owner):
    """Валидация владельца для удаления подписки."""
    return validate_subscription_owner(owner)
