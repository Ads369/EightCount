import threading
import uuid
import psycopg2
from postgres_repository import PostgresRepository

DSN = "postgresql://appuser:apppassword@localhost:5432/appdb"


def test_concurrent_inserts_dont_create_duplicates(pg_cleanup):
    """ИНТЕГРАЦИОННЫЙ ТЕСТ"""
    student_id = int(uuid.uuid4().int % 2_000_000_000)
    name = f"Concurrency Test Student {uuid.uuid4().hex[:8]}"
    pg_cleanup(student_id=student_id, name=name)

    conn = psycopg2.connect(dbname="appdb", user="appuser", password="apppassword", host="localhost", port="5432")
    with conn.cursor() as cur:
        cur.execute("DELETE FROM subscriptions WHERE student_id = %s", (student_id,))
        cur.execute("INSERT INTO students (id, name) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING", (student_id, name))
    conn.commit()

    errors = []

    def worker():
        try:
            dsn = "postgresql://appuser:apppassword@localhost:5432/appdb"
            repo = PostgresRepository(dsn=dsn)
            repo.add_visits_to_subscription(student_id=student_id, visits=1)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Ошибка конкурентности {errors}"

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*), SUM(total_visits) FROM subscriptions WHERE student_id = %s", (student_id,))
        count, total_visits = cur.fetchone()

        assert count == 1, f"Создалось {count} дублей подписки, ожидалось 1"
        assert total_visits == 5, f"Потеряли данные ожидалось 5 визитов а получили {total_visits}"
        conn.close()
