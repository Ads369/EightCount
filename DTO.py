from pydantic import BaseModel,Field


class StudentResponse(BaseModel):
    """Ответ: студант"""
    id : int
    name : str


class SubscriptionResponse(BaseModel):
    """Ответ: Подписка"""
    id : int
    owner : str
    total_visits : int