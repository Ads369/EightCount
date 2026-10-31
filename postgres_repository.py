import psycopg2
from psycopg2.extras import RealDictCursor

import logging
import os

from domain import Student, Subscription
from exceptions import DbError


logger = logging.getLogger(__name__)

class PostgresRepository:
    def __init__(self, dsn: str | None = None):
        self.dsn = dsn or os.environ.get(
            "DATABASE_URL",
            "postgresql://appuser:apppassword@postgres:5432/appdb",
        )
        self.init_db()

    def _get_connection(self):
        """Соединение с PostgreSQL. Курсор создаётся отдельно в каждом методе."""
        try:
            return psycopg2.connect(self.dsn, connect_timeout=3)
        except psycopg2.Error as e:
            logger.error(f"Не удалось подключиться к БД: {e}")
            raise DbError(f"Ошибка подключения к БД: {e}") from e

    def init_db(self):
        """Создаёт БД"""
        ddl = (
            """
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS subscriptions (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL UNIQUE
                    REFERENCES students(id) ON DELETE CASCADE,
                total_visits INTEGER NOT NULL DEFAULT 0
            )
            """,
        )
        conn = self._get_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    for statement in ddl:
                        cur.execute(statement)
        except psycopg2.Error as e:
            logger.error(f"Ошибка инициализации БД: {e}")
            raise DbError(f"Ошибка БД: {e}") from e
        finally:
            conn.close()

    def insert_student(self, name: str) -> int:
        """Добавляет ученика и возвращает его id."""
        conn = self._get_connection()
        try:
            with conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "INSERT INTO students (name) VALUES (%s) RETURNING id",
                        (name,),
                    )
                    return cur.fetchone()["id"]
        except psycopg2.Error as e:
            logger.error(f"Не получилось добавить ученика: {e}")
            raise DbError(f"Ошибка БД: {e}") from e
        finally:
            conn.close()

    def get_student_by_name(self, name: str):
        """Получить ученика по имени"""
        logger.info(f"Поиск студента в БД: {name}")
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, name FROM students WHERE name = %s", (name,)
                )
                row = cur.fetchone()
        except psycopg2.Error as e:
            logger.error(f"Ошибка БД: {e}")
            raise DbError(f"Ошибка БД: {e}") from e
        finally:
            conn.close()

        if row is None:
            logger.error(f"Ученик не найден в БД: {name}")
            return None

        logger.info(f"Ученик найден: id = {row['id']}, name = {row['name']}")
        return Student(id=row["id"], name=row["name"])

    def add_visits_to_subscription(self, student_id: int, visits: int):
        """Создаёт подписку или прибавляет занятия"""
        conn = self._get_connection()
        try:
            with conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "SELECT id, total_visits FROM subscriptions "
                        "WHERE student_id = %s FOR UPDATE",
                        (student_id,),
                    )
                    row = cur.fetchone()

                    if row is None:
                        cur.execute(
                            "INSERT INTO subscriptions (student_id, total_visits) "
                            "VALUES (%s, %s) "
                            "ON CONFLICT (student_id) DO UPDATE "
                            "SET total_visits = subscriptions.total_visits + EXCLUDED.total_visits "
                            "RETURNING id",
                            (student_id, visits),
                        )
                        sub_id = cur.fetchone()["id"]
                        logger.info(f"Создана/обновлена подписка для student_id = {student_id}")
                        return sub_id

                    new_total = row["total_visits"] + visits
                    cur.execute(
                        "UPDATE subscriptions SET total_visits = %s WHERE id = %s",
                        (new_total, row["id"]),
                    )
                    logger.info(f"Баланс подписок обновлён, новый баланс = {new_total}")
                    return row["id"]

        except psycopg2.Error as e:
            logger.error(f"Ошибка БД: {e}")
            raise DbError(f"Ошибка БД: {e}") from e
        finally:
            conn.close()

    def get_subscription_by_student_name(self, name: str):
        """Ишет подписку по имени"""
        logger.info(f"Поиск подписки для: {name}")
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT s.id AS sub_id, s.total_visits,
                           st.id AS student_id, st.name
                    FROM subscriptions s
                    JOIN students st ON st.id = s.student_id
                    WHERE st.name = %s
                    LIMIT 1
                    """,
                    (name,),
                )
                row = cur.fetchone()
        except psycopg2.Error as e:
            logger.error(f"Ошибка БД: {e}")
            raise DbError(f"Ошибка БД: {e}") from e
        finally:
            conn.close()

        if row is None:
            logger.error(f"Подписка не найдена для {name}")
            return None

        student = Student(id=row["student_id"], name=row["name"])
        return Subscription(
            owner=student,
            total_visits=row["total_visits"],
            id=row["sub_id"],
        )


    def update_subscription_visits(self, sub_id: int, total_visits: int):
        """Обновляет баланс подписки"""
        conn = self._get_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE subscriptions SET total_visits = %s WHERE id = %s",
                        (total_visits, sub_id),
                    )
        except psycopg2.Error as e:
            logger.error(f"Ошибка БД: {e}")
            raise DbError(f"Ошибка БД: {e}") from e
        finally:
            conn.close()


    def try_spend_visit(self, sub_id: int) -> int | None:
        """Атомарно списывает одно занятие.

        Проверка «хватает ли занятий» и вычитание — одной SQL-командой,
        поэтому параллельные запросы не спишут дважды. Возвращает остаток
        или None, если занятий нет.
        """
        conn = self._get_connection()
        try:
            with conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "UPDATE subscriptions SET total_visits = total_visits - 1 "
                        "WHERE id = %s AND total_visits > 0 "
                        "RETURNING total_visits",
                        (sub_id,),
                    )
                    row = cur.fetchone()
                    if row is None:
                        return None
                    return row["total_visits"]
        except psycopg2.Error as e:
            logger.error(f"Ошибка БД: {e}")
            raise DbError(f"Ошибка БД: {e}") from e
        finally:
            conn.close()


    def get_all_students(self) -> list[Student]:
        """Дай студентов"""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, name FROM students")
                rows = cur.fetchall()
        except psycopg2.Error as e:
            logger.error(f"Ошибка БД: {e}")
            raise DbError(f"Ошибка БД: {e}") from e
        finally:
            conn.close()

        return [Student(id=r["id"], name=r["name"]) for r in rows]


    def get_all_subscriptions(self):
        """Дай подписку"""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT s.id AS sub_id, s.total_visits,
                           st.id AS student_id, st.name
                    FROM subscriptions s
                    JOIN students st ON st.id = s.student_id
                    """
                )
                rows = cur.fetchall()
        except psycopg2.Error as e:
            logger.error(f"Ошибка БД: {e}")
            raise DbError(f"Ошибка БД: {e}") from e
        finally:
            conn.close()

        result = []
        for r in rows:
            student = Student(id=r["student_id"], name=r["name"])
            result.append(
                Subscription(
                    owner=student,
                    total_visits=r["total_visits"],
                    id=r["sub_id"],
                )
            )
        return result

    def delete_subscriptions_by_student(self, student_id: int):
        """Удали подписку по имени студента"""
        conn = self._get_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM subscriptions WHERE student_id = %s",
                        (student_id,),
                    )
        except psycopg2.Error as e:
            logger.error(f"Ошибка БД: {e}")
            raise DbError(f"Ошибка БД: {e}") from e
        finally:
            conn.close()

    def delete_student(self, student_id: int):
        """Удаляй студента"""
        conn = self._get_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM students WHERE id = %s", (student_id,)
                    )
        except psycopg2.Error as e:
            logger.error(f"Ошибка БД: {e}")
            raise DbError(f"Ошибка БД: {e}") from e
        finally:
            conn.close()
