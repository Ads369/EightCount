from fastapi import FastAPI

from app import Application
from routes import router
import logging



logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt= "%H:%M:%S"
)

application = Application("EightCount.db")
service = application.service

app = FastAPI(title="EightCount")
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
