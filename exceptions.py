class DomainError(Exception):
    """Может поймать всё сразу"""
    pass


class StudentNotFoundError(DomainError):
    """Ученик не найден в БД"""
    pass


class SubscriptionNotFoundError(DomainError):
    """"Подписка не найдена"""
    pass


class NoLessionsLeftError(DomainError):
    """У ученика закончились занятия"""
    pass