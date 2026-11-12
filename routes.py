import json
import uuid
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
import psycopg2

from app import Application
from exceptions import DbError
from dto.requests_dto import (
    AddSubscriptionRequest,
    AddStudentRequest,
    CheckInIn,
    DeleteStudent,
    DeleteSubscription,
)
from dto.responses_dto import StudentResponse, SubscriptionResponse

from kafka_integration.producer import send_event

application = Application()
service = application.service

router = APIRouter()

logger = logging.getLogger(__name__)


async def _emit_event(topic: str, action: str, data: dict) -> None:
    """Отправляет событие в Kafka. Key = event_id, Headers = topic, Value = {action, data}."""
    event_id = str(uuid.uuid4())
    value = {
        "action": action,
        "data": data,
    }
    headers = [("topic", topic.encode("utf-8"))]
    try:
        await send_event(topic, key=event_id, value=value, headers=headers)
    except Exception as e:
        logger.error(f"Не удалось отправить событие в Kafka: {e}")
        raise HTTPException(status_code=502, detail="Не удалось отправить событие в Kafka")


@router.get("/students", response_model=list[StudentResponse])
async def show_students():
    try:
        return service.get_all_students()
    except psycopg2.OperationalError:
        raise HTTPException(status_code=503, detail="БД временно недоступна")
    except DbError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subscriptions", response_model=list[SubscriptionResponse])
async def show_subscription():
    try:
        return service.get_all_subscription()
    except DbError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/students")
async def create_student(payload: AddStudentRequest):
    await _emit_event(
        "student.events",
        "student.created",
        {"name": payload.name},
    )
    return {"status": "queued"}


@router.post("/subscriptions")
async def create_subscription(payload: AddSubscriptionRequest):
    await _emit_event(
        "subscription.events",
        "subscription.created",
        {"owner": payload.owner, "total_visits": payload.total_visits},
    )
    return {"status": "queued"}


@router.post("/check-in")
async def check_in_route(payload: CheckInIn):
    await _emit_event(
        "checkin.events",
        "checkin.processed",
        {"owner": payload.owner},
    )
    return {"status": "queued"}


@router.delete("/students/{name}")
async def delete_student(name: str):
    await _emit_event(
        "student.events",
        "student.deleted",
        {"name": name},
    )
    return {"status": "queued"}


@router.delete("/subscription/{owner}")
async def delete_subscription(owner: str):
    await _emit_event(
        "subscription.events",
        "subscription.deleted",
        {"owner": owner},
    )
    return {"status": "queued"}
