from datetime import date, datetime
from typing import Annotated, Any, Dict, List, Literal, Optional

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from project.application.queries.page_request import MAX_PER_PAGE
from project.domain.models.enums.event_attendance_mode import EventAttendanceMode
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_reference_request_rejection_reason import (
    EventReferenceRequestRejectionReason,
)
from project.domain.models.enums.event_status import EventStatus
from project.domain.models.enums.event_target_group_origin import EventTargetGroupOrigin
from project.domain.models.enums.organization_verification_request_rejection_reason import (
    OrganizationVerificationRequestRejectionReason,
)
from project.presentation.bff.schemas import PageParams
from project.presentation.shared.event_rating import event_rating_choices
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
    # Whether the list may include the events the organization references.
    can_read_references: bool
    can_write_references: bool
    # Calendars of the organization (the filter and the assign modal); empty without
    # calendars:read.
    calendars: List["CalendarChoice"] = []
    can_write_calendars: bool = False


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
    # Also the events of other organizations this organization references.
    include_references: bool = False
    # Only the events of this calendar (own and foreign ones).
    calendar_id: Optional[int] = None

    @field_validator("*", mode="before")
    @classmethod
    def _empty_to_none(cls, value):
        return None if value == "" else value

    # "Before" validators run last-defined first, so this one sees the raw "".
    @field_validator("include_references", mode="before")
    @classmethod
    def _empty_to_false(cls, value):
        return False if value in ("", None) else value

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


class ManageEventDateParams(ManageEventListParams):
    """The list filter with a required date range; `page` and `sort` are ignored."""

    date_from: date
    date_to: date

    @model_validator(mode="after")
    def _validate_range(self):
        _check_range(self.date_from, self.date_to)
        return self


class ManageEventDateEvent(BaseModel):
    id: int
    name: str
    is_recurring: bool
    status: Optional[str] = None
    public_status: str
    organizer_name: Optional[str] = None
    place_label: Optional[str] = None
    # A referenced event of another organization (`organization_name` is its owner).
    is_reference: bool = False
    reference_id: Optional[int] = None
    organization_name: Optional[str] = None
    # Whether the organization owns the event (a calendar also holds foreign ones).
    is_own: bool = True


class ManageEventDate(BaseModel):
    id: int
    start: datetime
    end: Optional[datetime] = None
    allday: bool
    event: ManageEventDateEvent


class ManageEventDateList(BaseModel):
    items: List[ManageEventDate]
    truncated: bool


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
    # A referenced event of another organization (`organization_name` is its owner);
    # its internal tags and reference counts are left out.
    is_reference: bool = False
    reference_id: Optional[int] = None
    organization_name: Optional[str] = None
    # Whether the organization owns the event. Foreign rows (references or events of
    # a calendar) only offer the calendar action.
    is_own: bool = True


class ManageEventPage(BaseModel):
    items: List[ManageEventListItem]
    page: int
    per_page: int
    total: int
    pages: int
    organizer: Optional[ManageRef] = None
    event_place: Optional[ManageRef] = None


def _empty_to_none(value):
    return None if isinstance(value, str) and not value.strip() else value


class OrganizationLocation(BaseModel):
    street: Optional[str] = Field(default=None, max_length=255)
    postalCode: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10)
    ]
    city: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)
    ]
    state: Optional[str] = Field(default=None, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class OrganizationLogo(BaseModel):
    """An image field of a form (the organization logo, the place photo, the organizer
    logo)."""

    # A data URI; `None` on save keeps the stored image.
    image_base64: Optional[str] = None
    copyright_text: Optional[str] = Field(default=None, max_length=255)
    license_id: Optional[int] = None


class OrganizationSettingsVerificationRequests(BaseModel):
    allowed: bool = False
    text: Optional[str] = None
    postal_codes: List[
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=10)]
    ] = []


class OrganizationBaseSave(BaseModel):
    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=5, max_length=255)
    ]
    short_name: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True, min_length=5, max_length=100, pattern=r"^\w+$"
        ),
    ]
    description: Optional[str] = None
    location: OrganizationLocation
    logo: Optional[OrganizationLogo] = None
    url: Optional[str] = Field(default=None, max_length=255)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=255)
    fax: Optional[str] = Field(default=None, max_length=255)

    @field_validator("url", "email", "phone", "fax", mode="before")
    @classmethod
    def _contact_empty_to_none(cls, value):
        return _empty_to_none(value)


class OrganizationSettingsSave(OrganizationBaseSave):
    verification_requests: Optional[OrganizationSettingsVerificationRequests] = None


class OrganizationSettingsLocationView(BaseModel):
    """Stored locations may predate the required postal code and city."""

    street: str = ""
    postalCode: str = ""
    city: str = ""
    state: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class OrganizationSettingsForm(BaseModel):
    id: int
    name: str
    short_name: str
    description: Optional[str] = None
    location: OrganizationSettingsLocationView
    logo: Optional[OrganizationLogo] = None
    url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    can_verify_other: bool
    verification_requests: Optional[OrganizationSettingsVerificationRequests] = None
    licenses: List[PlanningChoice]
    deletion_requested_at: Optional[datetime] = None


class OrganizationNameAvailabilityParams(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    short_name: Optional[str] = Field(default=None, max_length=100)
    # Names of this organization do not count as taken (settings form).
    exclude_id: Optional[int] = None


class OrganizationNameAvailability(BaseModel):
    name_taken: Optional[bool] = None
    short_name_taken: Optional[bool] = None


class OrganizationCreateParams(BaseModel):
    invitation_id: Optional[int] = None


class OrganizationCreateRelation(BaseModel):
    """The relation to the current organization that is created along with the new
    one."""

    organization_name: str
    can_verify: bool
    can_auto_verify: bool


class OrganizationCreateForm(BaseModel):
    # Prefilled from the invitation, empty otherwise.
    name: str
    invitation_id: Optional[int] = None
    relation: Optional[OrganizationCreateRelation] = None
    licenses: List[PlanningChoice]


class OrganizationCreateSave(OrganizationBaseSave):
    invitation_id: Optional[int] = None
    relation_verify: bool = False
    relation_auto_verify_event_reference_requests: bool = False


class OrganizationCreated(BaseModel):
    id: int
    verified: bool
    redirect_url: str


class EventPlaceLocation(BaseModel):
    """An optional location (places, organizers): every part is optional."""

    street: Optional[str] = Field(default=None, max_length=255)
    postalCode: Optional[str] = Field(default=None, max_length=10)
    city: Optional[str] = Field(default=None, max_length=255)
    state: Optional[str] = Field(default=None, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @field_validator("street", "postalCode", "city", "state", mode="before")
    @classmethod
    def _empty_to_none(cls, value):
        return _empty_to_none(value)


class EventPlaceSave(BaseModel):
    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)
    ]
    url: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    location: EventPlaceLocation
    photo: Optional[OrganizationLogo] = None
    # Created from another form (a modal): no flash. Ignored on update.
    inline: bool = False

    @field_validator("url", mode="before")
    @classmethod
    def _url_empty_to_none(cls, value):
        return _empty_to_none(value)


class EventPlaceForm(BaseModel):
    # `None` and empty fields when creating.
    id: Optional[int] = None
    name: str = ""
    url: Optional[str] = None
    description: Optional[str] = None
    location: EventPlaceLocation
    photo: Optional[OrganizationLogo] = None
    licenses: List[PlanningChoice]


class EventPlaceSaved(BaseModel):
    id: int
    redirect_url: str


class EventPlaceNameAvailabilityParams(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    # The place itself does not count as taken (update form).
    exclude_id: Optional[int] = None


class EventPlaceNameAvailability(BaseModel):
    name_taken: Optional[bool] = None


class EventOrganizerSave(BaseModel):
    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)
    ]
    url: Optional[str] = Field(default=None, max_length=255)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=255)
    fax: Optional[str] = Field(default=None, max_length=255)
    location: EventPlaceLocation
    logo: Optional[OrganizationLogo] = None
    # Created from another form (a modal): no flash. Ignored on update.
    inline: bool = False

    @field_validator("url", "email", "phone", "fax", mode="before")
    @classmethod
    def _contact_empty_to_none(cls, value):
        return _empty_to_none(value)


class EventOrganizerForm(BaseModel):
    # `None` and empty fields when creating.
    id: Optional[int] = None
    name: str = ""
    url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    location: EventPlaceLocation
    logo: Optional[OrganizationLogo] = None
    licenses: List[PlanningChoice]


class EventOrganizerSaved(BaseModel):
    id: int
    redirect_url: str


class EventOrganizerNameAvailabilityParams(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    # The organizer itself does not count as taken (update form).
    exclude_id: Optional[int] = None


class EventOrganizerNameAvailability(BaseModel):
    name_taken: Optional[bool] = None


class EventDateDefinition(BaseModel):
    """One date of the event form. `start`/`end` are naive Berlin wall-clock times
    (`YYYY-MM-DDTHH:MM`), as the date and time inputs show them."""

    start: datetime
    end: Optional[datetime] = None
    allday: bool = False
    # The legacy RRULE subset (`RRULE:...`, `EXDATE:...`, `RDATE:...` lines).
    recurrence_rule: Optional[str] = None

    @field_validator("end", "recurrence_rule", mode="before")
    @classmethod
    def _empty_to_none(cls, value):
        return _empty_to_none(value)


class EventFormChoice(BaseModel):
    """An option of a select of the event form (enum values, ratings)."""

    value: int
    label: str


class CustomEventCategorySetChoice(BaseModel):
    id: int
    label: str
    selected: List[ManageRef] = []


class EventFormParams(BaseModel):
    # Copy the fields of this event ("use as template").
    template_id: Optional[int] = None


class EventForm(BaseModel):
    # `None` when creating.
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    date_definitions: List[EventDateDefinition]
    # Update only.
    status: Optional[int] = None
    public_status: int = int(EventPublicStatus.published)
    status_choices: List[EventFormChoice] = []
    public_status_choices: List[EventFormChoice] = []
    organizer: Optional[ManageRef] = None
    event_place: Optional[ManageRef] = None
    co_organizers: List[ManageRef] = []
    category_ids: List[int] = []
    category_choices: List[ManageRef]
    custom_category_sets: List[CustomEventCategorySetChoice] = []
    photo: Optional[OrganizationLogo] = None
    licenses: List[PlanningChoice]
    external_link: Optional[str] = None
    ticket_link: Optional[str] = None
    tags: Optional[str] = None
    internal_tags: Optional[str] = None
    kid_friendly: bool = False
    accessible_for_free: bool = False
    registration_required: bool = False
    booked_up: bool = False
    age_from: Optional[int] = None
    age_to: Optional[int] = None
    expected_participants: Optional[int] = None
    price_info: Optional[str] = None
    target_group_origin: int
    target_group_origin_choices: List[EventFormChoice]
    attendance_mode: int
    attendance_mode_choices: List[EventFormChoice]
    rating: int = 50
    rating_choices: List[EventFormChoice]
    # The organization's calendars the event is in; the field is hidden without
    # `calendars:write` or without calendars.
    calendars: List["CalendarChoice"] = []
    calendar_ids: List[int] = []
    # Create only: organizations that can be asked to reference the event.
    reference_request_choices: List[ManageRef] = []
    reference_request_ids: List[int] = []
    can_create_place: bool = False
    can_create_organizer: bool = False


def _url_field():
    return Field(default=None, max_length=255)


class EventSaveBase(BaseModel):
    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=3, max_length=255)
    ]
    description: Optional[str] = None
    date_definitions: List[EventDateDefinition] = Field(min_length=1)
    # Checked by the route (required, owned by the organization).
    organizer_id: Optional[int] = None
    event_place_id: Optional[int] = None
    co_organizer_ids: List[int] = []
    category_ids: List[int] = []
    custom_category_ids: List[int] = []
    photo: Optional[OrganizationLogo] = None
    external_link: Optional[str] = _url_field()
    ticket_link: Optional[str] = _url_field()
    tags: Optional[str] = None
    internal_tags: Optional[str] = None
    kid_friendly: bool = False
    accessible_for_free: bool = False
    registration_required: bool = False
    booked_up: bool = False
    age_from: Optional[int] = None
    age_to: Optional[int] = None
    expected_participants: Optional[int] = None
    price_info: Optional[str] = None
    target_group_origin: EventTargetGroupOrigin = EventTargetGroupOrigin.both
    attendance_mode: EventAttendanceMode = EventAttendanceMode.offline
    rating: int = 50
    # `None` leaves the calendars alone; a list needs `calendars:write` and sets them.
    calendar_ids: Optional[List[int]] = None

    @field_validator(
        "description",
        "external_link",
        "ticket_link",
        "tags",
        "internal_tags",
        "price_info",
        mode="before",
    )
    @classmethod
    def _text_empty_to_none(cls, value):
        return _empty_to_none(value)

    @field_validator("rating")
    @classmethod
    def _rating_is_offered(cls, value):
        if value not in [rating for rating, _ in event_rating_choices]:
            raise ValueError("rating is not one of the offered ratings")

        return value


class EventCreate(EventSaveBase):
    public_status: EventPublicStatus = EventPublicStatus.published
    # Only ids offered as `reference_request_choices`; sent when published.
    reference_request_ids: List[int] = []


class EventUpdate(EventSaveBase):
    status: EventStatus = EventStatus.scheduled
    public_status: EventPublicStatus = EventPublicStatus.published


class EventSaved(BaseModel):
    id: int
    redirect_url: str


class EventOccurrencesParams(BaseModel):
    """The preview of a recurrence rule. `start` is the naive Berlin wall-clock start of
    the date; `batch_start` pages the preview by ten."""

    start: datetime
    rrule: str = Field(max_length=10000)
    batch_start: int = Field(default=0, ge=0)


class EventOccurrence(BaseModel):
    # `YYYYMMDDTHHMMSS`, the value the rule's EXDATE/RDATE lines use.
    date: str
    formatted_date: str
    # `start`, `rrule`, `rdate` or `exdate`.
    type: str


class EventOccurrenceList(BaseModel):
    items: List[EventOccurrence]
    # Whether the next batch holds further occurrences.
    has_more: bool


class CustomEventCategoryLookupParams(ManageRefParams):
    set_id: int


class OrganizationRelationFormParams(BaseModel):
    """Prefill of the create form (`?target=<id>&verify=1`)."""

    target: Optional[int] = None
    verify: Optional[int] = None


class OrganizationRelationForm(BaseModel):
    # `id` is `None` and `target` the optional prefill when creating.
    id: Optional[int] = None
    target: Optional[ManageRef] = None
    verify: bool = False
    auto_verify_event_reference_requests: bool = False
    # The `verify` switch is only offered to organizations that may verify others.
    can_verify_other: bool
    list_url: str


class OrganizationRelationCreate(BaseModel):
    # Optional so that a missing organization is a field error of the form.
    target_admin_unit_id: Optional[int] = None
    verify: bool = False
    auto_verify_event_reference_requests: bool = False


class OrganizationRelationUpdate(BaseModel):
    verify: bool = False
    auto_verify_event_reference_requests: bool = False


class OrganizationRelationSaved(BaseModel):
    id: int
    redirect_url: str


class EventReferenceRequestForm(BaseModel):
    event: ManageRef
    list_url: str


class EventReferenceRequestCreate(BaseModel):
    # Optional so that a missing organization is a field error of the form.
    admin_unit_id: Optional[int] = None


class EventReferenceRequestSaved(BaseModel):
    id: int
    verified: bool
    redirect_url: str


class OrganizationExportFile(BaseModel):
    url: str
    size: int
    created_at: datetime


class OrganizationExport(BaseModel):
    file: Optional[OrganizationExportFile] = None


class OrganizationExportJob(BaseModel):
    # None when the export already ran eagerly and there is nothing to poll.
    job_id: Optional[str] = None


class OrganizationExportJobStatus(BaseModel):
    ready: bool
    successful: Optional[bool] = None


class ReviewChoice(BaseModel):
    value: int
    label: str


class ReviewContact(BaseModel):
    url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    # The location as one line, like `get_location_str`.
    address: Optional[str] = None


class ReviewOrganization(ReviewContact):
    id: int
    name: str
    is_verified: bool = False
    logo_url: Optional[str] = None
    description: Optional[str] = None


class ReviewOrganizationMember(BaseModel):
    email: str
    # Translated role titles.
    roles: List[str] = []


class ReviewEventPlace(BaseModel):
    name: str
    photo_url: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    address: Optional[str] = None
    # Set when the attendance mode is not offline, as on the old page.
    directions_url: Optional[str] = None


class ReviewEventOrganizer(BaseModel):
    name: str
    logo_url: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None


class ReviewCustomCategories(BaseModel):
    label: str
    names: List[str]


class ReviewEvent(BaseModel):
    id: int
    name: str
    # Raw enum names for the warning pills.
    public_status: Optional[str] = None
    status: Optional[str] = None
    booked_up: Optional[bool] = None
    attendance_mode: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    allday: bool = False
    # Translated; `None` where the old page hid the value (the default member).
    status_label: Optional[str] = None
    target_group_origin_label: Optional[str] = None
    attendance_mode_label: Optional[str] = None
    photo_url: Optional[str] = None
    description: Optional[str] = None
    price_info: Optional[str] = None
    external_link: Optional[str] = None
    ticket_link: Optional[str] = None
    category_names: List[str] = []
    custom_categories: List[ReviewCustomCategories] = []
    tags: Optional[str] = None
    kid_friendly: Optional[bool] = None
    accessible_for_free: Optional[bool] = None
    age_from: Optional[int] = None
    age_to: Optional[int] = None
    registration_required: Optional[bool] = None
    expected_participants: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    report_url: str
    place: Optional[ReviewEventPlace] = None
    organizer: Optional[ReviewEventOrganizer] = None
    co_organizers: List[ReviewEventOrganizer] = []
    organization: ReviewOrganization


class ReviewEventDate(BaseModel):
    id: int
    start: datetime


class EventReferenceRequestReview(BaseModel):
    id: int
    review_status: str
    event: ReviewEvent
    dates: List[ReviewEventDate] = []
    auto_verify: bool = False
    auto_verify_description: Optional[str] = None
    rating_choices: List[ReviewChoice]
    default_rating: int = 50
    rejection_reasons: List[ReviewChoice]
    list_url: str
    # The organization's calendars to put the event into with the accept (empty
    # without `calendars:write`).
    calendars: List["CalendarChoice"] = []


class OrganizationVerificationRequestReview(BaseModel):
    id: int
    review_status: str
    organization: ReviewOrganization
    members: List[ReviewOrganizationMember] = []
    auto_verify_description: str
    rejection_reasons: List[ReviewChoice]
    list_url: str


class EventReferenceRequestVerify(BaseModel):
    rating: int = 50
    auto_verify: bool = False
    # Also put the event into these calendars of the organization.
    calendar_ids: List[int] = []

    @field_validator("rating")
    @classmethod
    def _rating_is_offered(cls, value):
        if value not in [rating for rating, _ in event_rating_choices]:
            raise ValueError("rating is not one of the offered ratings")

        return value


class EventReferenceRequestReject(BaseModel):
    # `0` and `None` both mean no reason.
    rejection_reason: Optional[int] = None

    @field_validator("rejection_reason")
    @classmethod
    def _reason_is_known(cls, value):
        if value and value not in list(EventReferenceRequestRejectionReason):
            raise ValueError("rejection_reason is unknown")

        return value or None


class OrganizationVerificationRequestApprove(BaseModel):
    auto_verify: bool = False


class OrganizationVerificationRequestReject(BaseModel):
    rejection_reason: Optional[int] = None

    @field_validator("rejection_reason")
    @classmethod
    def _reason_is_known(cls, value):
        if value and value not in list(OrganizationVerificationRequestRejectionReason):
            raise ValueError("rejection_reason is unknown")

        return value or None


class RequestReviewed(BaseModel):
    redirect_url: str


# Lists, deletes and the event delete confirm (the "merge pages" slices)


class ManageNameConfirm(BaseModel):
    """Typed-name confirmation of a destructive action."""

    name: str = Field(min_length=1)


class ManageMessage(BaseModel):
    """The success text of a write done in a modal (the page stays)."""

    message: str


class ManageListPage(BaseModel):
    page: int
    per_page: int
    total: int
    pages: int
    can_write: bool


class ManageNamedListParams(PageParams):
    """Paging, search and sort of the organizer / place lists (50 rows like before)."""

    per_page: int = Field(default=50, ge=1, le=MAX_PER_PAGE)
    # The values of `EventOrganizerSort` / `EventPlaceSort`.
    sort: Optional[Literal["name", "-last_modified_at", "-number_of_events"]] = None
    keyword: Optional[str] = Field(default=None, max_length=255)


class EventOrganizerListItem(BaseModel):
    id: int
    name: str
    location: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    url: Optional[str] = None
    has_logo: bool = False
    number_of_events: int = 0
    last_modified_at: Optional[datetime] = None


class EventOrganizerListPage(ManageListPage):
    items: List[EventOrganizerListItem]


class EventPlaceListItem(BaseModel):
    id: int
    name: str
    location: Optional[str] = None
    has_coordinates: bool = False
    has_photo: bool = False
    number_of_events: int = 0
    last_modified_at: Optional[datetime] = None


class EventPlaceListPage(ManageListPage):
    items: List[EventPlaceListItem]


class EventDeleteForm(BaseModel):
    """What the event delete confirmation shows."""

    id: int
    name: str
    has_multiple_dates: bool


class EventDeleteSave(BaseModel):
    # Deleted from the event list (a modal): no flash.
    inline: bool = False


class EventDeleted(BaseModel):
    message: str
    redirect_url: str


class ManagePagedListParams(PageParams):
    """Paging of the reference lists (50 rows like before)."""

    per_page: int = Field(default=50, ge=1, le=MAX_PER_PAGE)


class ManageAudit(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by_label: Optional[str] = None
    updated_by_label: Optional[str] = None


class ManageDeleteSave(BaseModel):
    # Deleted from a list (a modal): no flash.
    inline: bool = False


class ManageDeleted(BaseModel):
    message: str
    redirect_url: str


class ManageIntChoice(BaseModel):
    value: int
    label: str


class EventReferenceListItem(BaseModel):
    id: int
    event_id: int
    event_name: str
    organization_id: int
    organization_name: str
    rating: Optional[int] = None
    created_at: Optional[datetime] = None


class IncomingEventReferenceListPage(ManageListPage):
    items: List[EventReferenceListItem]
    rating_choices: List[ManageIntChoice]
    can_assign_calendars: bool = False


class OutgoingEventReferenceListPage(ManageListPage):
    items: List[EventReferenceListItem]


class IncomingEventReferenceRead(BaseModel):
    id: int
    event_id: int
    event_name: str
    rating: Optional[int] = None
    rating_text: Optional[str] = None
    rating_choices: List[ManageIntChoice]
    audit: Optional[ManageAudit] = None
    can_write: bool
    can_assign_calendars: bool = False


class IncomingEventReferenceRating(BaseModel):
    rating: int

    @field_validator("rating")
    @classmethod
    def _known_rating(cls, value: int) -> int:
        if value not in [choice for choice, _ in event_rating_choices]:
            raise ValueError("Unknown rating")

        return value


class EventReferenceRequestListParams(ManagePagedListParams):
    # `EventReferenceRequestReviewStatus` value; -1 (the old "All") and empty: no filter.
    review_status: Optional[int] = None


class EventReferenceRequestListItem(BaseModel):
    id: int
    event_id: int
    event_name: str
    organization_id: int
    organization_name: str
    review_status: int
    review_status_label: str
    created_at: Optional[datetime] = None
    can_review: bool = False


class EventReferenceRequestListPage(ManageListPage):
    items: List[EventReferenceRequestListItem]
    review_status_choices: List[ManageIntChoice]


class OutgoingEventReferenceRequestRead(BaseModel):
    id: int
    event_id: int
    event_name: str
    review_status: int
    review_status_label: str
    rejection_reason_label: Optional[str] = None
    organization_id: int
    organization_name: str
    audit: Optional[ManageAudit] = None


# Relations and verification requests


class OrganizationRelationListParams(ManagePagedListParams):
    keyword: Optional[str] = Field(default=None, max_length=255)
    # The values of `OrganizationRelationSort`.
    sort: Optional[Literal["name", "-last_modified_at"]] = None
    # `1` / `0` like the old filters; empty: no filter.
    verify: Optional[bool] = None
    auto_verify_event_reference_requests: Optional[bool] = None


class OrganizationRelationListItem(BaseModel):
    id: int
    organization_id: int
    organization_name: str
    verify: bool = False
    auto_verify_event_reference_requests: bool = False
    last_modified_at: Optional[datetime] = None


class OrganizationRelationListPage(ManageListPage):
    items: List[OrganizationRelationListItem]
    # Without it the `verify` column and filter are not offered.
    can_verify_other: bool


class VerificationRequestListParams(ManagePagedListParams):
    # `OrganizationVerificationRequestReviewStatus` value; -1 (the old "All") and empty: no filter.
    review_status: Optional[int] = None


class VerificationRequestListItem(BaseModel):
    id: int
    organization_id: int
    organization_name: str
    review_status: int
    review_status_label: str
    created_at: Optional[datetime] = None
    can_review: bool = False


class IncomingVerificationRequestListPage(ManageListPage):
    items: List[VerificationRequestListItem]
    review_status_choices: List[ManageIntChoice]


class OutgoingVerificationRequestListPage(ManageListPage):
    items: List[VerificationRequestListItem]
    # An unverified organization without any request is led to the request dialog,
    # as the old list redirected to the verifier selection.
    suggest_create: bool = False


class OutgoingVerificationRequestRead(BaseModel):
    id: int
    organization_id: int
    organization_name: str
    review_status: int
    review_status_label: str
    rejection_reason_label: Optional[str] = None
    audit: Optional[ManageAudit] = None
    can_write: bool


class VerifierOrganization(BaseModel):
    id: int
    name: str
    is_verified: bool = False
    location: Optional[str] = None
    logo_url: Optional[str] = None
    description: Optional[str] = None
    incoming_verification_requests_text: Optional[str] = None
    # Whether the organization may ask this one (`CanRequestVerificationQuery`).
    can_request: bool = False


class VerifierOrganizationListPage(ManageListPage):
    items: List[VerifierOrganization]
    organization_name: str
    postal_code: Optional[str] = None


class VerificationRequestCreate(BaseModel):
    target_id: int


# Members and invitations


class MemberRole(BaseModel):
    name: str
    # Translated.
    title: str


class MemberListItem(BaseModel):
    id: int
    email: str
    roles: List[MemberRole]
    # The own membership cannot be removed here, `leave_url` is the page that does.
    is_current_user: bool = False
    leave_url: Optional[str] = None


class MemberListPage(ManageListPage):
    items: List[MemberListItem]
    role_choices: List[MemberRole]
    # Whether the "create" button (it leads to the invitation form) is offered.
    can_invite: bool


class MemberRolesSave(BaseModel):
    roles: List[str] = []


class MemberInvitationListItem(BaseModel):
    id: int
    email: str
    # The role names, for the roles modal.
    roles: List[str]


class MemberInvitationListPage(ManageListPage):
    items: List[MemberInvitationListItem]
    role_choices: List[MemberRole]


class MemberInvitationForm(BaseModel):
    role_choices: List[MemberRole]
    list_url: str


class MemberInvitationCreate(BaseModel):
    email: Annotated[EmailStr, Field(max_length=255)]
    roles: List[str] = []


class MemberInvitationSaved(BaseModel):
    id: int
    redirect_url: str


class OrganizationInvitationListItem(BaseModel):
    id: int
    email: str
    admin_unit_name: Optional[str] = None
    created_at: Optional[datetime] = None


class OrganizationInvitationListPage(ManageListPage):
    items: List[OrganizationInvitationListItem]


class OrganizationInvitationForm(BaseModel):
    # `None` and empty fields when creating.
    id: Optional[int] = None
    email: str = ""
    admin_unit_name: str = ""
    relation_verify: bool = False
    relation_auto_verify_event_reference_requests: bool = False
    # Without it the `relation_verify` switch is not offered.
    can_verify_other: bool
    audit: Optional[ManageAudit] = None
    list_url: str


class OrganizationInvitationUpdate(BaseModel):
    admin_unit_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)
    ]
    relation_verify: bool = False
    relation_auto_verify_event_reference_requests: bool = False


class OrganizationInvitationCreate(OrganizationInvitationUpdate):
    email: Annotated[EmailStr, Field(max_length=255)]


class OrganizationInvitationSaved(BaseModel):
    id: int
    redirect_url: str


class OrganizationsOverviewLink(BaseModel):
    """An invitation or organization of the current user and the page it leads to."""

    id: int
    name: str
    url: str


class OrganizationsOverview(BaseModel):
    invitations: List[OrganizationsOverviewLink]
    organization_invitations: List[OrganizationsOverviewLink]
    organizations: List[ManageRef]
    docs_url: Optional[str] = None
    # Whether the create form is open to the user (not closed, no deletion requested).
    can_create: bool
    # The organization the "Invite organization" button belongs to: the current one, when
    # it may invite other organizations.
    invite_organization_id: Optional[int] = None


HexColor = Annotated[str, StringConstraints(pattern=r"^#[0-9a-fA-F]{6}$")]


class WidgetSettingsForm(BaseModel):
    id: int
    font: str = ""
    background_color: str
    primary_color: str
    link_color: str
    # The embed instructions (script loader, the widget and the alternative iframe).
    loader_url: str
    iframe_url: str
    preview_url: str


class WidgetSettingsSave(BaseModel):
    font: Optional[Annotated[str, StringConstraints(max_length=255)]] = None
    background_color: Optional[HexColor] = None
    primary_color: Optional[HexColor] = None
    link_color: Optional[HexColor] = None


class OrganizationDeletionAnswer(BaseModel):
    redirect_url: str


# Organization API keys and OAuth2 clients


class ApiKeyListParams(PageParams):
    # The values of `ApiKeySort` (a plain literal keeps the OpenAPI parameter inline).
    sort: Optional[Literal["name", "-created_at"]] = None


class ApiKeyListItem(BaseModel):
    id: int
    name: str
    created_at: Optional[datetime] = None


class ApiKeyListPage(ManageListPage):
    items: List[ApiKeyListItem]


class ApiKeySave(BaseModel):
    name: str = Field(min_length=1)


class ApiKeyCreated(BaseModel):
    id: int
    # Only part of this answer, the read page never shows it again.
    key: str


class ApiKeyRead(BaseModel):
    id: int
    name: str
    created_at: Optional[datetime] = None
    rate_limits: List[str]
    audit: Optional[ManageAudit] = None
    can_write: bool


class ManageNameDeleteSave(BaseModel):
    """Typed-name confirmation; `inline` from a list (a modal) skips the flash."""

    name: str = Field(min_length=1)
    inline: bool = False


class OAuth2ClientListItem(BaseModel):
    id: int
    client_name: Optional[str] = None


class OAuth2ClientListPage(ManageListPage):
    items: List[OAuth2ClientListItem]


class OAuth2ClientForm(BaseModel):
    scopes: List[str]


class OAuth2ClientSave(BaseModel):
    client_name: str = Field(min_length=1)
    redirect_uris: List[str] = []
    scopes: List[str] = []


class OAuth2ClientSaved(BaseModel):
    id: int
    redirect_url: str


class OAuth2ClientRead(BaseModel):
    id: int
    client_id: str
    client_secret: Optional[str] = None
    client_name: Optional[str] = None
    client_uri: Optional[str] = None
    scope: str
    scopes: List[str]
    redirect_uris: List[str]
    grant_types: List[str]
    response_types: List[str]
    token_endpoint_auth_method: List[str]
    audit: Optional[ManageAudit] = None
    can_write: bool


# Apps, app keys, webhook deliveries and app installations


class AppListItem(BaseModel):
    id: int
    client_name: Optional[str] = None


class AppListPage(ManageListPage):
    items: List[AppListItem]


class AppPermissionChoice(BaseModel):
    permission: str
    label: str


class AppFormOptions(BaseModel):
    scopes: List[str]
    app_permissions: List[AppPermissionChoice]
    event_types: List[str]


class AppWebhookFields(BaseModel):
    url: Optional[Annotated[str, StringConstraints(max_length=255)]] = None
    secret: Optional[Annotated[str, StringConstraints(max_length=255)]] = None
    disabled: bool = False
    event_types: List[str] = []


class AppSave(BaseModel):
    client_name: str = Field(min_length=1)
    redirect_uris: List[str] = []
    scopes: List[str] = []
    app_permissions: List[str] = Field(min_length=1)
    homepage_url: Optional[Annotated[str, StringConstraints(max_length=255)]] = None
    setup_url: Optional[Annotated[str, StringConstraints(max_length=255)]] = None
    description: Optional[str] = None
    webhook: AppWebhookFields = AppWebhookFields()


class AppSaved(BaseModel):
    id: int
    redirect_url: str


class AppKeyItem(BaseModel):
    id: int
    kid: str
    checksum: str


class AppKeyCreated(BaseModel):
    id: int
    kid: str
    # Only part of this answer, never read again.
    private_pem: str


class AppRead(BaseModel):
    id: int
    client_id: str
    client_secret: Optional[str] = None
    client_name: Optional[str] = None
    client_uri: Optional[str] = None
    scope: str
    scopes: List[str]
    redirect_uris: List[str]
    grant_types: List[str]
    response_types: List[str]
    token_endpoint_auth_method: List[str]
    app_permissions: List[str]
    homepage_url: Optional[str] = None
    setup_url: Optional[str] = None
    webhook_url: Optional[str] = None
    description: Optional[str] = None
    keys: List[AppKeyItem]
    can_read_keys: bool
    can_write_keys: bool
    can_read_deliveries: bool
    audit: Optional[ManageAudit] = None
    can_write: bool


class WebhookDeliveryItem(BaseModel):
    id: int
    event_type: str
    timestamp: Optional[datetime] = None
    organization: Optional[str] = None


class WebhookDeliveryListPage(ManageListPage):
    items: List[WebhookDeliveryItem]
    app_title: str


class WebhookDeliveryRead(WebhookDeliveryItem):
    app_id: int
    app_title: str
    can_attempt: bool


class WebhookDeliveryAttemptItem(BaseModel):
    id: int
    start_at: datetime
    end_at: Optional[datetime] = None
    url: Optional[str] = None
    status: Optional[str] = None
    status_code: Optional[str] = None


class WebhookDeliveryAttemptListPage(ManageListPage):
    items: List[WebhookDeliveryAttemptItem]


class AppInstallationListItem(BaseModel):
    id: int
    app: Optional[str] = None
    created_at: Optional[datetime] = None


class AppInstallationListPage(ManageListPage):
    items: List[AppInstallationListItem]


class AppInstallationRead(BaseModel):
    id: int
    app: Optional[str] = None
    permissions: List[str]
    # The permissions the app requests now, set when they differ from the granted ones.
    requested_permissions: List[str]
    needs_permission_update: bool
    created_at: Optional[datetime] = None
    audit: Optional[ManageAudit] = None
    can_write: bool


class AppInstallationSaved(BaseModel):
    id: int
    redirect_url: str


class InstallableAppRead(BaseModel):
    id: int
    client_name: Optional[str] = None
    homepage_url: Optional[str] = None
    description: Optional[str] = None
    permissions: List[str]


class AppInstallSave(BaseModel):
    app_id: int


class CalendarChoice(BaseModel):
    id: int
    name: str
    private: bool = False


class CalendarListItem(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    private: bool = False
    number_of_events: int = 0
    last_modified_at: Optional[datetime] = None
    # Only public calendars have a public page.
    public_url: Optional[str] = None


class CalendarListPage(ManageListPage):
    items: List[CalendarListItem]


class CalendarForm(BaseModel):
    # `None` and empty fields when creating.
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    private: bool = False


class CalendarSave(BaseModel):
    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)
    ]
    description: Optional[str] = None
    private: bool = False
    # Created from another form (a modal): no flash.
    inline: bool = False

    @field_validator("description", mode="before")
    @classmethod
    def _description_empty_to_none(cls, value):
        return _empty_to_none(value)


class CalendarSaved(BaseModel):
    id: int
    redirect_url: str


class CalendarNameAvailabilityParams(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    # The calendar itself does not count as taken (update form).
    exclude_id: Optional[int] = None


class CalendarNameAvailability(BaseModel):
    name_taken: Optional[bool] = None


class CalendarChoices(BaseModel):
    items: List[CalendarChoice]


class EventCalendars(BaseModel):
    """The calendars of the organization and those the event is in."""

    choices: List[CalendarChoice]
    selected_ids: List[int]


class EventCalendarsSave(BaseModel):
    calendar_ids: List[int]
