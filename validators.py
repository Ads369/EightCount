from models import AddStudentRequest, AddSubscriptionRequest

def validate_add_student(name):
    """Валидирует add_student"""
    return AddStudentRequest(name=name)

def validate_add_subscription(owner, total_visits):
    """"Валидирует add_subscription"""
    return AddSubscriptionRequest(owner=owner, total_visits=total_visits)
