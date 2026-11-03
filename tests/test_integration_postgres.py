import threading
import uuid
import psycopg2
from postgres_repository import PostgresRepository

DSN = "postgresql://appuser:apppassword@localhost:5432/appdb"


def test_concurrent_spend_visit_postgres(pg_cleanup):
    """Интеграционный тест: реальная PostgreSQL, несколько потоков, атомарность списания."""
    student_id = int(uuid.uuid4().int % 2_000_000_000)
    name = f"Integration Student {uuid.uuid4().hex[:8]}"
    pg_cleanup(student_id=student_id, name=name)

    repo = PostgresRepository(dsn=DSN)

    conn = psycopg2.connect(dbname="appdb", user="appuser", password="apppassword", host="localhost", port="5432")
    with conn.cursor() as cur:
        cur.execute("DELETE FROM subscriptions WHERE student_id = %s", (student_id,))
        cur.execute(
            "INSERT INTO students (id, name) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING",
            (student_id, name),
        )
    conn.commit()

    sub_id = repo.add_visits_to_subscription(student_id=student_id, visits=5)

    errors = []
    spent = []

    def worker():
        try:
            remaining = repo.try_spend_visit(sub_id)
            if remaining is not None:
                spent.append(remaining)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Ошибки конкурентности: {errors}"
    assert len(spent) == 5, f"Ожидалось 5 списаний, получили {len(spent)}"

    sixth = repo.try_spend_visit(sub_id)
    assert sixth is None, "Баланс ушёл в минус после исчерпания занятий"

    with conn.cursor() as cur:
        cur.execute("SELECT total_visits FROM subscriptions WHERE student_id = %s", (student_id,))
        row = cur.fetchone()
        assert row[0] == 0, f"Ожидался остаток 0, получено {row[0]}"
    conn.close()


def test_concurrent_upsert_no_duplicates_postgres(pg_cleanup):
    """Интеграционный тест: upsert подписки не создаёт дубли при конкурентном добавлении."""
    student_id = int(uuid.uuid4().int % 2_000_000_000)
    name = f"Integration Student {uuid.uuid4().hex[:8]}"
    pg_cleanup(student_id=student_id, name=name)

    repo = PostgresRepository(dsn=DSN)

    conn = psycopg2.connect(dbname="appdb", user="appuser", password="apppassword", host="localhost", port="5432")
    with conn.cursor() as cur:
        cur.execute("DELETE FROM subscriptions WHERE student_id = %s", (student_id,))
        cur.execute(
            "INSERT INTO students (id, name) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING",
            (student_id, name),
        )
    conn.commit()

    errors = []

    def worker():
        try:
            repo.add_visits_to_subscription(student_id=student_id, visits=1)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Ошибки конкурентного upsert: {errors}"

    sub = repo.get_subscription_by_student_name(name)
    assert sub is not None, "Подписка не найдена"
    assert sub.total_visits == 5, f"Ожидалось 5 визитов, получено {sub.total_visits}"

    conn.close()
