from storage import (
    init_db,
)

from service import demo

def main():
   """Создаёт БД и запускает проверку"""
   init_db()
   demo()

if __name__ == "__main__":
    main()
