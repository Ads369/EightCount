from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ValidationError
from app import Application
from exceptions import DomainError, DbError, StudentAlreadyExistError, StudentNotFoundError, SubscriptionNotFoundError
from requests_dto import AddSubscriptionRequest, AddStudentRequest, CheckInIn, DeleteStudent, DeleteSubscription
from responses_dto import StudentResponse, SubscriptionResponse
import logging

application = Application("EightCount.db")
service = application.service

router = APIRouter()

logger = logging.getLogger(__name__)

@router.get("/students", response_model=list[StudentResponse])
def show_students():
    return service.get_all_students()

@router.get("/subscriptions", response_model=list[SubscriptionResponse])
def show_subscription():
    return service.get_all_subscription()

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


@router.delete("/subscription/{owner}")
def delete_subscription(owner:str):
    try:
        result = service.remove_subscription(owner)
        return {"status": result}
    except StudentNotFoundError as e:
        raise HTTPException(status_code=404, detail=(str(e)))
    except SubscriptionNotFoundError as e:
        raise HTTPException(status_code=404, detail=(str(e)))
    except DbError as e:
        raise HTTPException(status_code=404, detail=(str(e)))


@router.delete("/students/{name}")
def delete_student(name:str):
    try:
        result = service.remove_student(name)
        return {"status": result}
    except StudentNotFoundError as e:
        raise HTTPException(status_code=400, detail=(str(e)))
    except SubscriptionNotFoundError as e:
        raise HTTPException(status_code=404, detail=(str(e)))
    except DbError as e:
        raise HTTPException(status_code=500, detail=(str(e)))