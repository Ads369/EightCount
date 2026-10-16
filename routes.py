from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ValidationError
from app import Application
from exceptions import DomainError, DbError, StudentAlreadyExistError
from models import AddSubscriptionRequest, AddStudentRequest, CheckInIn


application = Application("EightCount.db")
service = application.service

router = APIRouter()


@router.get("/students")
def show_students():
    students = service.get_all_students()
    return [
        {"id": s.id, "name": s.name}
        for s in students
    ]

@router.post("/students")
def create_student(payload: AddStudentRequest):
    try:
        result = service.add_student(payload.name)
        return {"status": result}
    except StudentAlreadyExistError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except DbError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/subscriptions")
def create_subscription(payload: AddSubscriptionRequest):
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
