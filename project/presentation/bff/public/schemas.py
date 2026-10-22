from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from project.application.read_models.organization_read_models import (
    OrganizationListItemReadModel,
)
from project.application.read_models.page import Page
from project.presentation.bff.schemas import PageParams


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


class PublicOrganizationListParams(PageParams):
    keyword: Optional[str] = Field(default=None, max_length=255)


class PublicOrganizationRow(BaseModel):
    id: int
    name: str
    short_name: Optional[str] = None
    is_verified: bool = False


class PublicOrganizationPage(BaseModel):
    items: List[PublicOrganizationRow]
    page: int
    per_page: int
    total: int
    pages: int

    @classmethod
    def from_page(
        cls, page: Page[OrganizationListItemReadModel]
    ) -> "PublicOrganizationPage":
        return cls(
            items=[
                PublicOrganizationRow(
                    id=o.id,
                    name=o.name,
                    short_name=o.short_name,
                    is_verified=o.is_verified,
                )
                for o in page.items
            ],
            page=page.page,
            per_page=page.per_page,
            total=page.total,
            pages=page.pages,
        )


class PublicOrganizationRelation(BaseModel):
    """The relation card of the visitor's current organization to this one."""

    source: PublicOrganizationRef
    relation_id: Optional[int] = None
    verify: bool = False
    auto_verify_event_reference_requests: bool = False
    edit_url: Optional[str] = None
    create_url: Optional[str] = None


class PublicOrganization(BaseModel):
    id: int
    name: str
    short_name: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    description: Optional[str] = None
    is_verified: bool = False
    location: Optional[PublicOrganizerLocation] = None
    logo_url: Optional[str] = None
    ical_url: str
    relation: Optional[PublicOrganizationRelation] = None
