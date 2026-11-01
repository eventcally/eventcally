from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from project.application.queries.page_request import (
    DEFAULT_PER_PAGE,
    MAX_PER_PAGE,
    PageRequest,
)
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


class WidgetEventDateParams(PageParams):
    per_page: int = Field(default=10, ge=1, le=50)
    organization_id: Optional[int] = None
    date_from: date
    date_to: Optional[date] = None
    keyword: Optional[str] = Field(default=None, max_length=255)
    category_id: List[int] = []


class OrganizationWidgetEventDateParams(BaseModel):
    """The query of the legacy iframe widget page, kept lenient like its WTForms form:
    the dates and the category are plain strings that the route parses."""

    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=DEFAULT_PER_PAGE, ge=1)
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    keyword: Optional[str] = Field(default=None, max_length=255)
    category_id: Optional[str] = None
    tag: Optional[str] = Field(default=None, max_length=255)

    @field_validator("per_page")
    @classmethod
    def clamp_per_page(cls, value: int) -> int:
        return min(value, MAX_PER_PAGE)

    def to_page_request(self) -> PageRequest:
        return PageRequest(page=self.page, per_page=self.per_page)


class WidgetPhoto(BaseModel):
    url_200: str
    url_500: str
    copyright_text: Optional[str] = None
    license_code: Optional[str] = None
    license_url: Optional[str] = None


class WidgetEvent(BaseModel):
    id: int
    name: str
    description_preview: Optional[str] = None
    status: Optional[str] = None
    public_status: str
    booked_up: Optional[bool] = None
    attendance_mode: Optional[str] = None
    organization_id: int
    organization_name: str
    organizer_name: Optional[str] = None
    place_name: Optional[str] = None
    photo: Optional[WidgetPhoto] = None


class WidgetEventDate(BaseModel):
    id: int
    start: datetime
    end: Optional[datetime] = None
    allday: bool
    event: WidgetEvent


class WidgetEventDatePage(BaseModel):
    items: List[WidgetEventDate]
    page: int
    per_page: int
    total: int
    pages: int


class WidgetCategory(BaseModel):
    id: int
    name: str


class WidgetCategoryList(BaseModel):
    items: List[WidgetCategory]


class PublicChoice(BaseModel):
    value: str
    label: str


class PublicDistance(BaseModel):
    value: int
    label: str


class EventDateSearchParams(PageParams):
    per_page: int = Field(default=50, ge=1, le=50)
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    keyword: Optional[str] = Field(default=None, max_length=255)
    category_id: List[int] = []
    tag: Optional[str] = Field(default=None, max_length=255)
    admin_unit_id: Optional[int] = None
    organizer_id: Optional[int] = None
    postal_code: Optional[str] = Field(default=None, max_length=255)
    coordinate: Optional[str] = Field(
        default=None, pattern=r"^-?\d+(\.\d+)?,-?\d+(\.\d+)?$"
    )
    distance: Optional[int] = None
    created_at_from: Optional[date] = None
    created_at_to: Optional[date] = None
    sort: Literal["start", "-created_at"] = "start"
    exclude_recurring: bool = False
    not_referenced: bool = False


class EventDateSearchOptionsParams(BaseModel):
    admin_unit_id: Optional[int] = None
    organizer_id: Optional[int] = None


class EventDateSearchOptions(BaseModel):
    default_date_from: date
    categories: List[WidgetCategory]
    distances: List[PublicDistance]
    sorts: List[PublicChoice]
    organization: Optional[PublicOrganizationRef] = None
    organizer: Optional[PublicOrganizationRef] = None
    referencing_organization: Optional[PublicOrganizationRef] = None


class PublicEventDatePlace(BaseModel):
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PublicEventReference(BaseModel):
    state: Literal["own", "none", "referenced"]
    reference_id: Optional[int] = None


class PublicEventDateEvent(BaseModel):
    id: int
    name: str
    description_preview: Optional[str] = None
    status: Optional[str] = None
    public_status: str
    booked_up: Optional[bool] = None
    attendance_mode: Optional[str] = None
    organization: PublicOrganizationRef
    organizer_name: Optional[str] = None
    place: Optional[PublicEventDatePlace] = None
    photo: Optional[WidgetPhoto] = None
    reference: Optional[PublicEventReference] = None


class PublicEventDate(BaseModel):
    id: int
    start: datetime
    end: Optional[datetime] = None
    allday: bool
    event: PublicEventDateEvent


class PublicEventDatePage(BaseModel):
    items: List[PublicEventDate]
    page: int
    per_page: int
    total: int
    pages: int


class PublicOrganizerListParams(PageParams):
    per_page: int = Field(default=5, ge=1, le=50)
    keyword: Optional[str] = Field(default=None, max_length=255)


class PublicOrganizerRefPage(BaseModel):
    items: List[PublicOrganizationRef]
    page: int
    per_page: int
    total: int
    pages: int
