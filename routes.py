from fastapi import APIRouter
from pydantic import BaseModel

from service import add_student, add_subscription, check_in

router = APIRouter()


class StudentIn(BaseModel):
    name: str


class SubscriptionIn(BaseModel):
    owner: str
    count_lession: int = 0


class CheckInIn(BaseModel):
    owner: str


@router.post("/students")
def create_student(payload: StudentIn):
    add_student(payload.name)
    return {"status": "ok"}


@router.post("/subscriptions")
def create_subscription(payload: SubscriptionIn):
    result = add_subscription(payload.owner, payload.count_lession)
    return {"status": result or "ok"}


@router.post("/check-in")
def check_in_route(payload: CheckInIn):
    return {"result": check_in(payload.owner)}
