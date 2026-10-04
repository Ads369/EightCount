import sqlite3
import logging
from domain import Student, Subscription

logger = logging.getLogger(__name__)

class SqliteRepository:
    def __init__(self, db_path: str = "EightCount.db"):
        self.db_path = db_path

    def _get_connection(self):
        """Соединение с БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def init_db(self):
        conn = self._get_connection()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            total_visits INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (student_id) REFERENCES students(id)
        );
    """)
        conn.commit()
        conn.close()

    def insert_student(self, name: str):
        """Добавляем студента"""
        conn = self._get_connection()
        cur = conn.execute("INSERT INTO students (name) VALUES (?)", (name,))
        conn.commit()
        student_id = cur.lastrowid
        conn.close()
        return student_id


    def get_student_by_name(self, name:str):
        """Ищет студента по имени"""
        logger.debug(f"Поиск стулента в БД: {name}")

        conn = self._get_connection()
        row = conn.execute(
            "SELECT id, name FROM students WHERE name = ?", (name,)
        ).fetchone()
        conn.close()

        if row is None:
            logger.debug(f"Ученик не найден в БД: {name}")
            return None
        
        logger.debug(f"Ученик найден: id={row['id']}, name={row['name']}")
        return Student(id=row["id"], name=row["name"])

    def insert_subscription(self, student_id:int, total_visits: int):
        """Добавляем подписку"""
        conn = self._get_connection()
        cur = conn.execute(
            "INSERT INTO subscriptions (student_id, total_visits) VALUES (?, ?)",
            (student_id, total_visits)
        )
        conn.commit()
        sub_id = cur.lastrowid
        conn.close()
        return sub_id

    def get_subscription_by_student_name(self, name: str):
        """Ищет подписку по имени студента"""
        logger.debug(f'Поиск подписки для: {name}')

        conn = self._get_connection()
        row = conn.execute("""
            SELECT s.id AS sub_id, s.total_visits,
                st.id AS student_id, st.name
            FROM subscriptions s
            JOIN students st ON st.id = s.student_id
            WHERE st.name = ?
            LIMIT 1
        """, (name,)).fetchone()
        conn.close()

        if row is None:
            logger.debug(f'Подписка не найдена для {name}')
            return None
        
        student = Student(id=row["student_id"], name=row["name"])
        return Subscription(
            owner=student,
            total_visits=row["total_visits"],
            id=row["sub_id"]
        )

    def update_subscription_visits(self, sub_id:int, total_visits:int):
        """Обновляет баланс"""
        conn = self._get_connection()
        conn.execute(
            "UPDATE subscriptions SET total_visits = ? WHERE id = ?",
            (total_visits, sub_id)
        )
        conn.commit()
        conn.close()

    def get_all_students(self) -> list[Student]:
        """Все пользователи из БД"""
        conn = self._get_connection()
        rows = conn.execute("SELECT id, name FROM students").fetchall()
        conn.close()
        return [Student(id=r["id"], name=r["name"]) for r in rows]

    def get_all_subscriptions(self):
        """Все подписки из БД"""
        conn = self._get_connection()
        rows = conn.execute("""
            SELECT s.id AS sub_id, s.total_visits,
                st.id AS student_id, st.name
            FROM subscriptions s
            JOIN students st ON st.id = s.student_id
        """).fetchall()
        conn.close()
        result = []
        for r in rows:
            student = Student(id=r["student_id"], name=r["name"])
            result.append(Subscription(
                owner=student,
                total_visits = r["total_visits"],
                id = r['sub_id']
            ))
        return result

    def delete_subscription_student(self, student_id:int):
        "Удалить подписку у пользователя"
        conn= self._get_connection()
        conn.execute(
            "DELETE  FROM subscriptions WHERE student_id = ?",
            (student_id,)
        )
        conn.commit()
        conn.close()

    def delete_student(self, student_id:int):
        "Удалить пользователя"
        conn = self._get_connection()
        conn.execute(
            "DELETE FROM students WHERE id = ?",
            (student_id,)
        )
        conn.commit()
        conn.close()
