"""Интеграционные тесты PostgresRepository на реальной PostgreSQL.

Проверяем два свойства, которые нельзя доказать на моках:

1. Атомарность — конкурентные списания не уводят баланс в минус и не
   списывают одно занятие дважды; конкурентные пополнения не теряют визиты.
2. Идемпотентность — инициализация схемы, создание подписки (одна строка
   на ученика) и удаление можно повторять без побочных эффектов.

Каждый тест работает с уникальными именами (uuid) и регистрирует созданные
строки в фикстуре ``pg_cleanup``. Она удаляет подписки и учеников даже если
тест упал, поэтому прогон не оставляет мусора и не зависит от других тестов.

Запуск::

    DATABASE_URL=postgresql://appuser:apppassword@localhost:5432/appdb \
        pytest tests/test_integration_postgres.py -v
"""

import os
import threading
import uuid

import pytest

from domain import Student
from exceptions import DbError
from postgres_repository import PostgresRepository

DEFAULT_DSN = "postgresql://appuser:apppassword@localhost:5432/appdb"


@pytest.fixture(scope="module")
def dsn() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DSN)


@pytest.fixture(scope="module")
def repo(dsn: str) -> PostgresRepository:
    """Один репозиторий на модуль. Конструктор сам создаёт схему."""
    try:
        return PostgresRepository(dsn=dsn)
    except DbError as exc:  # БД не поднята — это не падение кода, а среда
        pytest.skip(f"PostgreSQL недоступен по DSN {dsn!r}: {exc}")


@pytest.fixture
def make_student(repo: PostgresRepository, pg_cleanup):
    """Создаёт уникального ученика и гарантирует его удаление после теста."""

    def factory(prefix: str = "itest-student") -> Student:
        name = f"{prefix}-{uuid.uuid4().hex[:12]}"
        student_id = repo.insert_student(name)
        pg_cleanup(student_id=student_id, name=name)
        return Student(name=name, id=student_id)

    return factory


def subscriptions_of(repo: PostgresRepository, student_id: int) -> list:
    """Все подписки конкретного ученика (в базе их должна быть максимум одна)."""
    return [sub for sub in repo.get_all_subscriptions() if sub.owner.id == student_id]


def run_concurrently(worker, attempts: int, timeout: float = 30.0):
    """Запускает ``attempts`` потоков одновременно на общем барьере.

    Барьер нужен, чтобы потоки стартовали максимально синхронно и реально
    конкурировали за строку, а не выполнялись по очереди.

    Возвращает ``(results, errors)``: результаты успешных вызовов и список
    исключений. Ошибки не пробрасываются, чтобы тест мог показать их все сразу.
    """
    barrier = threading.Barrier(attempts)
    results: list = []
    errors: list = []

    def target(index: int) -> None:
        try:
            barrier.wait(timeout=timeout)
            results.append(worker(index))
        except BaseException as exc:  # noqa: BLE001 - фиксируем всё, включая timeouts
            errors.append(exc)

    threads = [
        threading.Thread(target=target, args=(index,), name=f"worker-{index}")
        for index in range(attempts)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=timeout)

    alive = [thread.name for thread in threads if thread.is_alive()]
    assert not alive, f"Потоки зависли и не завершились: {alive}"
    return results, errors


# ---------------------------------------------------------------------------
# Идемпотентность схемы и учеников
# ---------------------------------------------------------------------------


def test_init_db_is_idempotent(repo: PostgresRepository, make_student) -> None:
    """Повторная инициализация схемы не ломает существующие данные."""
    repo.init_db()
    repo.init_db()

    student = make_student()
    assert repo.get_student_by_name(student.name).id == student.id


def test_student_roundtrip_and_unknown_name(
    repo: PostgresRepository, make_student
) -> None:
    student = make_student()

    found = repo.get_student_by_name(student.name)
    assert isinstance(found, Student)
    assert (found.id, found.name) == (student.id, student.name)

    missing_name = f"missing-{uuid.uuid4().hex}"
    assert repo.get_student_by_name(missing_name) is None
    assert student.id in {item.id for item in repo.get_all_students()}


def test_duplicate_student_name_raises_and_keeps_one_row(
    repo: PostgresRepository, make_student
) -> None:
    """Уникальность имени держит БД, а не только проверка в сервисе.

    Гонка «проверили — не нашли — вставили» должна упираться в UNIQUE,
    а не создавать двух одинаковых учеников.
    """
    student = make_student()

    with pytest.raises(DbError):
        repo.insert_student(student.name)

    matches = [item for item in repo.get_all_students() if item.name == student.name]
    assert len(matches) == 1
    assert matches[0].id == student.id


# ---------------------------------------------------------------------------
# Создание и пополнение подписки
# ---------------------------------------------------------------------------


def test_add_visits_creates_single_subscription(
    repo: PostgresRepository, make_student
) -> None:
    student = make_student()

    sub_id = repo.add_visits_to_subscription(student.id, 3)

    subscription = repo.get_subscription_by_student_name(student.name)
    assert subscription is not None
    assert (subscription.id, subscription.total_visits) == (sub_id, 3)
    assert (subscription.owner.id, subscription.owner.name) == (
        student.id,
        student.name,
    )
    assert len(subscriptions_of(repo, student.id)) == 1


def test_repeated_add_visits_keeps_one_subscription_but_sums_balance(
    repo: PostgresRepository, make_student
) -> None:
    """Повторный вызов идемпотентен по строке подписки, но не по балансу.

    Одна подписка на ученика сохраняется, а визиты суммируются — это
    осознанная семантика «пополнения», а не повторной доставки команды.
    """
    student = make_student()

    first_id = repo.add_visits_to_subscription(student.id, 2)
    second_id = repo.add_visits_to_subscription(student.id, 3)

    assert first_id == second_id
    subscription = repo.get_subscription_by_student_name(student.name)
    assert subscription is not None
    assert subscription.total_visits == 5
    assert len(subscriptions_of(repo, student.id)) == 1


def test_add_visits_for_unknown_student_rolls_back(
    repo: PostgresRepository,
) -> None:
    """Ошибка FK не должна оставлять «осиротевшую» подписку."""
    missing_id = -1

    with pytest.raises(DbError):
        repo.add_visits_to_subscription(missing_id, 5)

    assert subscriptions_of(repo, missing_id) == []


def test_concurrent_add_visits_creates_exactly_one_subscription(
    repo: PostgresRepository, make_student
) -> None:
    """Гонка на первом пополнении не должна создать дубли подписки."""
    student = make_student()
    attempts = 8

    results, errors = run_concurrently(
        lambda _: repo.add_visits_to_subscription(student.id, 1), attempts
    )

    assert errors == [], f"Ошибки конкурентного создания подписки: {errors!r}"
    assert len(results) == attempts
    assert len(set(results)) == 1, f"Создано несколько подписок: {results}"

    subscription = repo.get_subscription_by_student_name(student.name)
    assert subscription is not None
    assert subscription.total_visits == attempts
    assert len(subscriptions_of(repo, student.id)) == 1


def test_concurrent_add_visits_to_existing_subscription_does_not_lose_updates(
    repo: PostgresRepository, make_student
) -> None:
    """Параллельные пополнения существующей подписки не теряют визиты."""
    student = make_student()
    sub_id = repo.add_visits_to_subscription(student.id, 1)
    attempts = 10
    visits_per_attempt = 2

    results, errors = run_concurrently(
        lambda _: repo.add_visits_to_subscription(student.id, visits_per_attempt),
        attempts,
    )

    assert errors == [], f"Ошибки конкурентного пополнения: {errors!r}"
    assert set(results) == {sub_id}

    subscription = repo.get_subscription_by_student_name(student.name)
    assert subscription is not None
    assert subscription.total_visits == 1 + visits_per_attempt * attempts
    assert len(subscriptions_of(repo, student.id)) == 1


# ---------------------------------------------------------------------------
# Атомарное списание занятий
# ---------------------------------------------------------------------------


def test_try_spend_visit_decrements_and_stops_at_zero(
    repo: PostgresRepository, make_student
) -> None:
    student = make_student()
    sub_id = repo.add_visits_to_subscription(student.id, 2)

    assert repo.try_spend_visit(sub_id) == 1
    assert repo.try_spend_visit(sub_id) == 0
    assert repo.try_spend_visit(sub_id) is None
    assert repo.try_spend_visit(sub_id) is None

    subscription = repo.get_subscription_by_student_name(student.name)
    assert subscription is not None
    assert subscription.total_visits == 0


def test_try_spend_visit_unknown_subscription_returns_none(
    repo: PostgresRepository,
) -> None:
    assert repo.try_spend_visit(-1) is None


def test_concurrent_spend_never_overspends(
    repo: PostgresRepository, make_student
) -> None:
    """Главный тест атомарности: N потоков не могут списать больше баланса.

    Каждое успешное списание возвращает новый остаток, поэтому успешные
    значения обязаны быть уникальными: {4, 3, 2, 1, 0} для баланса 5.
    Повтор значения означал бы двойное списание одной строки.
    """
    student = make_student()
    initial_visits = 5
    attempts = 20
    sub_id = repo.add_visits_to_subscription(student.id, initial_visits)

    results, errors = run_concurrently(
        lambda _: repo.try_spend_visit(sub_id), attempts
    )

    assert errors == [], f"Ошибки конкурентного списания: {errors!r}"

    success_values = [value for value in results if value is not None]
    assert len(success_values) == initial_visits, (
        f"Успешных списаний {len(success_values)}, ожидалось {initial_visits}"
    )
    assert set(success_values) == set(range(initial_visits)), (
        f"Остатки повторяются или выходят за диапазон: {sorted(success_values)}"
    )

    subscription = repo.get_subscription_by_student_name(student.name)
    assert subscription is not None
    assert subscription.total_visits == 0


def test_concurrent_spend_with_single_visit_has_exactly_one_winner(
    repo: PostgresRepository, make_student
) -> None:
    """При балансе 1 из 10 одновременных попыток проходит ровно одна."""
    student = make_student()
    sub_id = repo.add_visits_to_subscription(student.id, 1)

    results, errors = run_concurrently(
        lambda _: repo.try_spend_visit(sub_id), attempts=10
    )

    assert errors == [], f"Ошибки конкурентного списания: {errors!r}"
    winners = [value for value in results if value is not None]
    assert winners == [0], f"Ожидался ровно один победитель, получено: {winners}"

    subscription = repo.get_subscription_by_student_name(student.name)
    assert subscription is not None
    assert subscription.total_visits == 0


def test_concurrent_add_and_spend_keeps_balance_consistent(
    repo: PostgresRepository, make_student
) -> None:
    """Пополнения и списания вперемешку не теряют обновления друг друга."""
    student = make_student()
    initial_visits = 10
    adders = 5
    spenders = 5
    visits_per_add = 3
    sub_id = repo.add_visits_to_subscription(student.id, initial_visits)

    def workload(index: int):
        if index < adders:
            return "add", repo.add_visits_to_subscription(student.id, visits_per_add)
        return "spend", repo.try_spend_visit(sub_id)

    results, errors = run_concurrently(workload, attempts=adders + spenders)

    assert errors == [], f"Ошибки смешанной конкурентной нагрузки: {errors!r}"
    added_ids = [value for kind, value in results if kind == "add"]
    spent_values = [value for kind, value in results if kind == "spend"]

    assert set(added_ids) == {sub_id}
    assert all(value is not None for value in spent_values), (
        f"Не хватило занятий при балансе {initial_visits}: {spent_values}"
    )

    expected = initial_visits + visits_per_add * adders - spenders
    subscription = repo.get_subscription_by_student_name(student.name)
    assert subscription is not None
    assert subscription.total_visits == expected


# ---------------------------------------------------------------------------
# Удаление: идемпотентность и каскад
# ---------------------------------------------------------------------------


def test_delete_subscription_is_idempotent_and_keeps_student(
    repo: PostgresRepository, make_student
) -> None:
    student = make_student()
    repo.add_visits_to_subscription(student.id, 4)

    repo.delete_subscriptions_by_student(student.id)
    repo.delete_subscriptions_by_student(student.id)  # повторно — не ошибка

    assert repo.get_subscription_by_student_name(student.name) is None
    assert subscriptions_of(repo, student.id) == []
    assert repo.get_student_by_name(student.name).id == student.id


def test_delete_student_cascades_subscription_and_is_idempotent(
    repo: PostgresRepository, make_student
) -> None:
    student = make_student()
    repo.add_visits_to_subscription(student.id, 2)

    repo.delete_student(student.id)
    repo.delete_student(student.id)  # повторное удаление — не ошибка

    assert repo.get_student_by_name(student.name) is None
    assert repo.get_subscription_by_student_name(student.name) is None
    assert subscriptions_of(repo, student.id) == []
