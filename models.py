from enum import Enum
from pydantic import UUID4, BaseModel, Field
from datetime import datetime


class Status(str, Enum):
    PENDING = "pending"
    ERROR = "error"
    COMPLETED = "completed"


class StatusResponse(BaseModel):
    status: Status


class JobResponse(BaseModel):
    id: UUID4
    webhook_url: str
    created_at: datetime
    duration: float
    status: str


class TranslationRequest(BaseModel):
    duration: float = Field(description="configurable delay in seconds")
    webhook_url: str = Field(
        description="url endpoint to notify once the translation is completed"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {"duration": 30.5, "webhook_url": "https://webhook.site/94070b61-3ca5-4a17-8fc0-db7b8a8c1c8c"}
            ]
        }