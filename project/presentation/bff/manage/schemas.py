from datetime import date, datetime
from typing import Annotated, Any, Dict, List, Literal, Optional

from pydantic import (
    BaseModel,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_status import EventStatus
from project.presentation.bff.schemas import PageParams
from project.presentation.shared.search_options import distance_choices

# A month view with leading and trailing weeks spans at most 42 days.
MAX_RANGE_DAYS = 62
DISTANCES = [value for value, _ in distance_choices]
COORDINATE_PATTERN = r"^-?\d+(\.\d+)?,-?\d+(\.\d+)?$"


def _check_range(date_from: date, date_to: date) -> None:
    if date_to < date_from:
        raise ValueError("date_to must not be before date_from")

    if (date_to - date_from).days > MAX_RANGE_DAYS:
        raise ValueError(f"The range must not exceed {MAX_RANGE_DAYS} days")


class PlanningChoice(BaseModel):
    id: int
    name: str


class PlanningDistance(BaseModel):
    value: int
    label: str


class PlanningExternalCalendar(BaseModel):
    title: str
    url: str
    active: bool = False


class PlanningOptions(BaseModel):
    categories: List[PlanningChoice]
    distances: List[PlanningDistance]
    external_calendars: List[PlanningExternalCalendar]
    max_dates: int


class PlanningEventDateParams(BaseModel):
    date_from: date
    date_to: date
    category_id: List[int] = []
    postal_code: Optional[str] = Field(default=None, max_length=255)
    coordinate: Optional[str] = Field(default=None, pattern=COORDINATE_PATTERN)
    distance: Optional[int] = None
    expected_participants_min: Optional[int] = Field(default=None, ge=0)
    exclude_recurring: bool = False

    @model_validator(mode="after")
    def _validate(self):
        _check_range(self.date_from, self.date_to)

        if self.distance is not None and self.distance not in DISTANCES:
            raise ValueError("distance is not one of the offered radii")

        return self


class PlanningEvent(BaseModel):
    id: int
    name: str
    status: Optional[str] = None
    public_status: str
    booked_up: Optional[bool] = None
    attendance_mode: Optional[str] = None
    has_status_info: bool
    organization_name: str
    organizer_name: Optional[str] = None
    place_name: Optional[str] = None


class PlanningEventDate(BaseModel):
    id: int
    start: datetime
    end: Optional[datetime] = None
    allday: bool
    event: PlanningEvent


class PlanningEventDateList(BaseModel):
    items: List[PlanningEventDate]
    truncated: bool


class ExternalCalendarEventParams(BaseModel):
    url: str = Field(max_length=2048)
    date_from: date
    date_to: date

    @model_validator(mode="after")
    def _validate(self):
        _check_range(self.date_from, self.date_to)
        return self


class ExternalCalendarEvent(BaseModel):
    name: str
    start: str
    end: Optional[str] = None
    allday: bool
    location: Optional[str] = None
    description: Optional[str] = None


class ExternalCalendarEventList(BaseModel):
    url: str
    items: List[ExternalCalendarEvent]


class CustomWidgetListParams(PageParams):
    pass


class CustomWidgetListItem(BaseModel):
    id: int
    name: str
    widget_type: str


class CustomWidgetPage(BaseModel):
    items: List[CustomWidgetListItem]
    page: int
    per_page: int
    total: int
    pages: int
    can_write: bool


class CustomWidgetForm(BaseModel):
    id: int
    organization_id: int
    widget_type: str
    name: str
    settings: Dict[str, Any] = {}


class CustomWidgetSave(BaseModel):
    widget_type: Literal["search", "calendar"]
    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=3, max_length=255)
    ]
    settings: Dict[str, Any] = {}


class CustomWidgetCreated(BaseModel):
    id: int


class EventReferenceCreate(BaseModel):
    event_id: int


class EventReferenceCreated(BaseModel):
    id: int


class ManageChoice(BaseModel):
    value: int
    name: str
    label: str


class ManageEventListOptions(BaseModel):
    categories: List[PlanningChoice]
    statuses: List[ManageChoice]
    public_statuses: List[ManageChoice]
    distances: List[PlanningDistance]
    default_date_from: date
    can_write: bool
    can_request_reference: bool


class ManageEventListParams(PageParams):
    keyword: Optional[str] = Field(default=None, max_length=255)
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    category_id: Optional[int] = None
    tag: Optional[str] = Field(default=None, max_length=255)
    internal_tag: Optional[str] = Field(default=None, max_length=255)
    organizer_id: Optional[int] = None
    event_place_id: Optional[int] = None
    postal_code: Optional[str] = Field(default=None, max_length=255)
    radius_coordinate: Optional[str] = Field(default=None, pattern=COORDINATE_PATTERN)
    radius_distance: Optional[int] = None
    status: Optional[int] = None
    public_status: Optional[int] = None
    created_at_from: Optional[date] = None
    created_at_to: Optional[date] = None
    is_recurring: Optional[Literal["0", "1"]] = None
    sort: Literal["min_start", "-last_modified_at", "-created_at"] = "min_start"

    @field_validator("*", mode="before")
    @classmethod
    def _empty_to_none(cls, value):
        return None if value == "" else value

    @model_validator(mode="after")
    def _validate(self):
        if self.radius_distance is not None and self.radius_distance not in DISTANCES:
            raise ValueError("radius_distance is not one of the offered radii")

        if self.status is not None and self.status not in list(EventStatus):
            raise ValueError("status is unknown")

        if self.public_status is not None and self.public_status not in list(
            EventPublicStatus
        ):
            raise ValueError("public_status is unknown")

        return self


class ManageRef(BaseModel):
    id: int
    name: str


class ManageRefParams(BaseModel):
    keyword: Optional[str] = Field(default=None, max_length=255)


class ManageRefList(BaseModel):
    items: List[ManageRef]


class ManageEventListItem(BaseModel):
    id: int
    name: str
    start: Optional[datetime] = None
    allday: bool = False
    is_recurring: bool
    number_of_dates: Optional[int] = None
    organizer_name: Optional[str] = None
    place_label: Optional[str] = None
    category_names: List[str]
    tags: Optional[str] = None
    internal_tags: Optional[str] = None
    status: Optional[str] = None
    public_status: str
    has_photo: bool
    number_of_references: Optional[int] = None
    number_of_reference_requests: Optional[int] = None
    last_modified_at: Optional[datetime] = None


class ManageEventPage(BaseModel):
    items: List[ManageEventListItem]
    page: int
    per_page: int
    total: int
    pages: int
    organizer: Optional[ManageRef] = None
    event_place: Optional[ManageRef] = None
