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
from project.domain.models.enums.event_reference_request_rejection_reason import (
    EventReferenceRequestRejectionReason,
)
from project.domain.models.enums.event_status import EventStatus
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
    """An image field of a form (the organization logo, the place photo)."""

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
    """Every part of a place location is optional."""

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
