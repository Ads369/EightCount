from fastapi import FastAPI

from routes import router

from storage import (
    init_db,
)

from service import demo


app = FastAPI(title="EightCount")
app.include_router(router)

def main():
   """Создаёт БД и запускает проверку"""
   init_db()
   demo()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
