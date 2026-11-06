import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ValidationError
from app import Application
from exceptions import DomainError, DbError, StudentAlreadyExistError, StudentNotFoundError, SubscriptionNotFoundError
from requests_dto import AddSubscriptionRequest, AddStudentRequest, CheckInIn, DeleteStudent, DeleteSubscription
from responses_dto import StudentResponse, SubscriptionResponse
from fastapi import HTTPException
import logging

from kafka.producer import send_event, flush

application = Application()
service = application.service

router = APIRouter()

logger = logging.getLogger(__name__)


def _emit_event(topic: str, action: str, key: str, data: dict) -> None:
    """Отправляет событие в Kafka. Ошибка Kafka не ломает основной ответ."""
    event = {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "action": action,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        send_event(topic, key, json.dumps(event, ensure_ascii=False))
        flush()
    except Exception as e:
        logger.error(f"Не удалось отправить событие в Kafka: {e}")


@router.get("/students", response_model=list[StudentResponse])
def show_students():
    try:
        return service.get_all_students()
    except psycopg2.OperationalError:
        raise HTTPException(status_code = 503, detail= "БД временно недоступна")


@router.get("/subscriptions", response_model=list[SubscriptionResponse])
def show_subscription():
    return service.get_all_subscription()


@router.post("/students")
def create_student(payload: AddStudentRequest):
    try:
        result = service.add_student(payload.name)
        _emit_event("student.events", "student.created", payload.name, {"name": payload.name, "id": result[1]})
        return {"status": result}
    except StudentAlreadyExistError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except DbError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subscriptions")
def create_subscription(payload: AddSubscriptionRequest):
    try:
        result = service.add_subscription(payload.owner, payload.total_visits)
        _emit_event(
            "subscription.events",
            "subscription.created",
            payload.owner,
            {"owner": payload.owner, "total_visits": payload.total_visits, "id": result},
        )
        return {"status": result}
    except StudentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DbError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-in")
def check_in_route(payload: CheckInIn):
    try:
        result = service.check_in(payload.owner)
        _emit_event(
            "checkin.events",
            "checkin.processed",
            payload.owner,
            {"owner": payload.owner, "remaining_visits": result},
        )
        return {"status": "ok", "message": result}
    except DomainError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DbError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/subscription/{owner}")
def delete_subscription(owner: str):
    try:
        result = service.remove_subscription(owner)
        _emit_event("subscription.events", "subscription.deleted", owner, {"owner": owner})
        return {"status": result}
    except StudentNotFoundError as e:
        raise HTTPException(status_code=404, detail=(str(e)))
    except SubscriptionNotFoundError as e:
        raise HTTPException(status_code=404, detail=(str(e)))
    except DbError as e:
        raise HTTPException(status_code=404, detail=(str(e)))


@router.delete("/students/{name}")
def delete_student(name: str):
    try:
        result = service.remove_student(name)
        _emit_event("student.events", "student.deleted", name, {"name": name})
        return {"status": result}
    except StudentNotFoundError as e:
        raise HTTPException(status_code=400, detail=(str(e)))
    except SubscriptionNotFoundError as e:
        raise HTTPException(status_code=404, detail=(str(e)))
    except DbError as e:
        raise HTTPException(status_code=500, detail=(str(e)))
