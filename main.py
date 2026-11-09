import uuid
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from routes import router
from kafka_integration.producer import start_producer, stop_producer, send_event
from kafka_integration.config import TOPIC_STUDENT_EVENTS

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start"""
    await start_producer()
    yield
    """off"""
    await stop_producer()


app = FastAPI(lifespan=lifespan)
app.include_router(router)

