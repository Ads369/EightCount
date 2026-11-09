import json
import uuid
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ValidationError
import psycopg2

from app import Application
from exceptions import (
    DomainError,
    DbError,
    StudentAlreadyExistError,
    StudentNotFoundError,
    SubscriptionNotFoundError,
)
from requests_dto import (
    AddSubscriptionRequest,
    AddStudentRequest,
    CheckInIn,
    DeleteStudent,
    DeleteSubscription,
)
from responses_dto import StudentResponse, SubscriptionResponse

from kafka_integration.producer import send_event

application = Application()
service = application.service

router = APIRouter()

logger = logging.getLogger(__name__)


async def _emit_event(topic: str, action: str, data: dict) -> None:
    """Отправляет событие в Kafka. Ошибка Kafka не ломает основной ответ."""
    event = {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "action": action,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        await send_event(topic, event)
    except Exception as e:
        logger.error(f"Не удалось отправить событие в Kafka: {e}")


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
    try:
        result = service.add_student(payload.name)
        await _emit_event(
            "student.events",
            "student.created",
            {"name": payload.name, "id": result[1]},
        )
        return {"status": result}
    except StudentAlreadyExistError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except DbError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subscriptions")
async def create_subscription(payload: AddSubscriptionRequest):
    try:
        result = service.add_subscription(payload.owner, payload.total_visits)
        await _emit_event(
            "subscription.events",
            "subscription.created",
            {
                "owner": payload.owner,
                "total_visits": payload.total_visits,
                "id": result,
            },
        )
        return {"status": result}
    except StudentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DbError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-in")
async def check_in_route(payload: CheckInIn):
    try:
        result = service.check_in(payload.owner)
        await _emit_event(
            "checkin.events",
            "checkin.processed",
            {"owner": payload.owner, "remaining_visits": result},
        )
        return {"status": "ok", "message": result}
    except DomainError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DbError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/subscription/{owner}")
async def delete_subscription(owner: str):
    try:
        result = service.remove_subscription(owner)
        await _emit_event(
            "subscription.events",
            "subscription.deleted",
            {"owner": owner},
        )
        return {"status": result}
    except StudentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SubscriptionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DbError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/students/{name}")
async def delete_student(name: str):
    try:
        result = service.remove_student(name)
        await _emit_event(
            "student.events",
            "student.deleted",
            {"name": name},
        )
        return {"status": result}
    except StudentNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SubscriptionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DbError as e:
        raise HTTPException(status_code=500, detail=str(e))
