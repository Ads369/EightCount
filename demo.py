from service import (
    SubscriptionService,
)

service = SubscriptionService()


def main():
    """Создаёт БД и запускает проверку"""
    print(service.add_student("Алексей"))
    # print(add_subscription("Алексей", 2))
    # print(check_in("Алексей"))
    # print_students()
    # print_subscriptions()
    # print(remove_student_with_sub("Алексей"))


if __name__ == "__main__":
    print("qwe")
    main()
