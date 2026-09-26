from main import Subscription, Student


def test_success_visit():
    student = Student("Test", 1000)
    sub = Subscription(600, student)

    result = sub.check_in()
    assert result == "Успешно"
    assert student.balance == 400 
    assert sub.total_visits == 1

def test_failure_visit():
    student = Student("Test", 500)
    sub = Subscription(1000, student)
    
    result = sub.check_in()
    assert result == "Недостаточно средств"
    assert student.balance == 500
    assert sub.total_visits == 0
    assert len(sub.visit_log) == 0
