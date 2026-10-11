from pydantic import BaseModel,Field

class AddStudentRequest(BaseModel):
    """Модель для ученика"""
    name: str = Field(min_lenght=1, max_lenght=100)


class AddSubscriptionRequest(BaseModel):
    """Модель для подписки"""
    owner: str = Field(min_lenght=1, max_lenght=200)
    total_visits: int = Field(gt=0, le=1000)