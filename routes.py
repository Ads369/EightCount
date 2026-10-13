from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ValidationError
from app import Application
from exceptions import DomainError, DbError


router = APIRouter()

application = Application("EightCount.db")
service = application.service

router = APIRouter()

class StudentIn(BaseModel):
    name: str


class SubscriptionIn(BaseModel):
    owner: str
    total_visits: int = 0


class CheckInIn(BaseModel):
    owner: str


@router.post("/students")
def create_student(payload: StudentIn):
    result = service.add_student(payload.name)
    return {"status": result}


@router.post("/subscriptions")
def create_subscription(payload: SubscriptionIn):
    result = service.add_subscription(payload.owner, payload.total_visits)
    return {"status": result}


@router.post("/check-in")
def check_in_route(payload: CheckInIn):
    try:
        result = service.check_in(payload.owner)
        return {"status": "ok", "message": result}
    except DomainError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DbError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=404, detail=(e))
