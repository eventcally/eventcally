from pydantic import BaseModel, EmailStr, Field


class EventReportForm(BaseModel):
    event_id: int
    event_name: str


class EventReportCreate(BaseModel):
    contact_name: str = Field(min_length=5, max_length=255)
    contact_email: EmailStr = Field(max_length=255)
    message: str = Field(min_length=20, max_length=1000)
