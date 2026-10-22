from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class EventReportForm(BaseModel):
    event_id: int
    event_name: str


class EventReportCreate(BaseModel):
    contact_name: str = Field(min_length=5, max_length=255)
    contact_email: EmailStr = Field(max_length=255)
    message: str = Field(min_length=20, max_length=1000)


class PublicOrganizerLocation(BaseModel):
    street: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None


class PublicOrganizationRef(BaseModel):
    id: int
    name: str


class PublicOrganizer(BaseModel):
    id: int
    name: str
    url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    location: Optional[PublicOrganizerLocation] = None
    logo_url: Optional[str] = None
    organization: PublicOrganizationRef
    ical_url: str
