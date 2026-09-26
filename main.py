# ## UseCase:
# 1. Человек приходит
# 2. Администратор прожимает кнопку "Пришёл"
# 3. Проверяет есть ли у пользователя деньги на счету 
# 4. Если есть - списывает 
# 5. Записывает дату и время
# 6. Сиестема должна показать "Успешно" или "Недостаточно средств"
from storage import students, subscriptions
from service import add_student, add_subscription, check_in



add_student("Алексей")
add_student('Роман')
# add_student("Коля")


add_subscription('Алексей', 2)
add_subscription('Роман', 1)
# add_subscription("Коля", 2)

print(check_in("Алексей"))
print(check_in("Алексей"))
print(check_in("Алексей"))
print(check_in("Роман"))
# # print(check_in("Роман"))
# print(check_in("Коля"))

print(students)
print(subscriptions)

