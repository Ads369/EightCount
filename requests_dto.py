from pydantic import BaseModel,Field

class AddStudentRequest(BaseModel):
    """Модель для ученика"""
    name: str = Field(min_length=1, max_length=100)


class AddSubscriptionRequest(BaseModel):
    """Модель для подписки"""
    # owner: str = Field(min_length=1, max_length=200)
    total_visits: int = Field(gt=0, le=1000)


class CheckInIn(BaseModel):
    """Модель проверки"""
    owner: str = Field(min_length=1, max_length=200)


class DeleteSubscription(BaseModel):
    """Модель для удаление подписки"""
    owner: str = Field(min_length=1, max_length=200)


class DeleteStudent(BaseModel):
    """Модель для удаление ученика"""
    name: str = Field(min_length=1, max_length=200)