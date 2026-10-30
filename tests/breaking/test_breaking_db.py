import pytest
import psycopg2
from postgres_repository import PostgresRepository

@pytest.fixture
def repo():
    dsn = "postgresql://appuser:apppassword@localhost:5432/appdb"
    
    conn = psycopg2.connect(dsn)
    repository = PostgresRepository(dsn=dsn)
    yield repository, conn
    conn.close()

def test_repository_handles_missing_table_gracefully(repo):
    repository, conn = repo
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE students RENAME TO students_broken;")
    conn.commit()    

    try:
        with pytest.raises(Exception) as exc_info:
            repository.get_all_students()
            assert "students" in str(exc_info.value) or "relation" in str(exc_info.value) or "DbError" in str(exc_info.value)
    finally:
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE students_broken RENAME TO students;")
        conn.commit()