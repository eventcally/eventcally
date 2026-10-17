"""Read models of the event and event-date queries.

Attribute names equal what the templates, `jsonld`, the iCal builder and the marshmallow
schemas read from the ORM objects, so they render unchanged. Collections keep the load
order of the ORM relationships.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel
from project.application.read_models.image_read_model import (
    ImageEditReadModel,
    ImageReadModel,
)
from project.application.read_models.location_read_model import LocationReadModel
from project.application.read_models.reference_data_read_models import (
    CustomEventCategorySetRefReadModel,
    EventCategoryRefReadModel,
)
from project.domain.models.enums.event_attendance_mode import EventAttendanceMode
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_reference_request_rejection_reason import (
    EventReferenceRequestRejectionReason,
)
from project.domain.models.enums.event_reference_request_review_status import (
    EventReferenceRequestReviewStatus,
)
from project.domain.models.enums.event_status import EventStatus
from project.domain.models.enums.event_target_group_origin import EventTargetGroupOrigin
from project.domain.types.object_id import ObjectId


class EventDateDefinitionDetailReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    id: ObjectId
    start: datetime
    end: Optional[datetime] = None
    allday: bool = False
    recurrence_rule: Optional[str] = None


class EventCustomCategoryReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    label: Optional[str] = None
    category_set: CustomEventCategorySetRefReadModel

    @property
    def category_set_id(self) -> ObjectId:
        return self.category_set.id

    @property
    def label_or_name(self) -> str:
        return self.label or self.name


class EventOrganizerEmbedReadModel(BaseReadModel):
    """An organizer inside an event (`OrganizerSearchItemSchema`, the detail page)."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    location: Optional[LocationReadModel] = None
    logo: Optional[ImageReadModel] = None

    @property
    def logo_id(self) -> Optional[ObjectId]:
        return self.logo.id if self.logo else None


class EventPlaceEmbedReadModel(BaseReadModel):
    """A place inside an event (`PlaceSearchItemSchema`, the detail page)."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    url: Optional[str] = None
    description: Optional[str] = None
    admin_unit_id: Optional[ObjectId] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    location: Optional[LocationReadModel] = None
    photo: Optional[ImageReadModel] = None

    @property
    def photo_id(self) -> Optional[ObjectId]:
        return self.photo.id if self.photo else None


class EventOrganizationReadModel(BaseReadModel):
    """The owning organization inside an event (`OrganizationSearchItemSchema`)."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    short_name: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    description: Optional[str] = None
    is_verified: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    location: Optional[LocationReadModel] = None
    logo: Optional[ImageReadModel] = None

    @property
    def logo_id(self) -> Optional[ObjectId]:
        return self.logo.id if self.logo else None


class OrganizationBadgeReadModel(BaseReadModel):
    """An organization as a link with its verified badge."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    is_verified: bool = False


class EventReferenceItemReadModel(BaseReadModel):
    """An organization that references the event."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    admin_unit: OrganizationBadgeReadModel


class EventReferenceRequestItemReadModel(BaseReadModel):
    """A reference request the event's organization sent."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    review_status: Optional[EventReferenceRequestReviewStatus] = None
    rejection_reason: Optional[EventReferenceRequestRejectionReason] = None
    admin_unit: OrganizationBadgeReadModel


class VerifierOrganizationReadModel(EventOrganizationReadModel):
    """An organization that can verify others, as the request selection shows it."""

    incoming_verification_requests_text: Optional[str] = None


class EventSearchItemReadModel(BaseReadModel):
    """An event as the searches, lists and the manage list show it
    (`EventSearchItemSchema`). `internal_tags` is `None` unless the caller may read
    the organization's private events; `reference_id` is set when the calling
    organization references the event."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    description: Optional[str] = None
    external_link: Optional[str] = None
    ticket_link: Optional[str] = None
    tags: Optional[str] = None
    internal_tags: Optional[str] = None
    kid_friendly: Optional[bool] = None
    accessible_for_free: Optional[bool] = None
    age_from: Optional[int] = None
    age_to: Optional[int] = None
    target_group_origin: Optional[EventTargetGroupOrigin] = None
    attendance_mode: Optional[EventAttendanceMode] = None
    status: Optional[EventStatus] = None
    public_status: EventPublicStatus = EventPublicStatus.published
    registration_required: Optional[bool] = None
    booked_up: Optional[bool] = None
    expected_participants: Optional[int] = None
    price_info: Optional[str] = None
    rating: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    admin_unit_id: ObjectId
    organizer_id: ObjectId
    event_place_id: ObjectId
    is_recurring: bool = False
    reference_id: Optional[ObjectId] = None
    number_of_dates: Optional[int] = None
    number_of_references: Optional[int] = None
    number_of_reference_requests: Optional[int] = None
    date_definitions: List[EventDateDefinitionDetailReadModel] = []
    photo: Optional[ImageReadModel] = None
    event_place: Optional[EventPlaceEmbedReadModel] = None
    organizer: Optional[EventOrganizerEmbedReadModel] = None
    admin_unit: EventOrganizationReadModel
    categories: List[EventCategoryRefReadModel] = []
    custom_categories: List[EventCustomCategoryReadModel] = []

    @property
    def photo_id(self) -> Optional[ObjectId]:
        return self.photo.id if self.photo else None

    def has_multiple_dates(self) -> bool:
        return self.is_recurring or len(self.date_definitions) > 1

    @property
    def category(self) -> Optional[EventCategoryRefReadModel]:
        return self.categories[0] if self.categories else None

    @property
    def last_modified_at(self) -> Optional[datetime]:
        return self.updated_at if self.updated_at else self.created_at

    @property
    def min_start_definition(self) -> Optional[EventDateDefinitionDetailReadModel]:
        if not self.date_definitions:
            return None

        return min(self.date_definitions, key=lambda d: d.start)

    @property
    def custom_categories_by_set(
        self,
    ) -> Dict[ObjectId, List[EventCustomCategoryReadModel]]:
        by_set: Dict[ObjectId, List[EventCustomCategoryReadModel]] = {}

        for category in self.custom_categories:
            by_set.setdefault(category.category_set.id, []).append(category)

        return by_set


class EventDetailReadModel(EventSearchItemReadModel):
    """The event page, the API detail (`EventSchema`) and the iCal feeds.

    The audit labels and the reference requests are private: the handler clears
    them for actors without the matching permissions."""

    co_organizers: List[EventOrganizerEmbedReadModel] = []
    references: List[EventReferenceItemReadModel] = []
    reference_requests: List[EventReferenceRequestItemReadModel] = []
    created_by_label: Optional[str] = None
    updated_by_label: Optional[str] = None


class EventEditReadModel(EventDetailReadModel):
    """Fills the manage update form (attribute names equal the form field names) and
    backs the delete confirmation; the photo carries its data."""

    photo: Optional[ImageEditReadModel] = None


class EventDateReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    id: ObjectId
    start: datetime
    end: Optional[datetime] = None
    allday: bool = False


class EventDateSearchHitReadModel(EventDateReadModel):
    """A row of the event-date searches and the widget (`EventDateSearchItemSchema`)."""

    event: EventSearchItemReadModel


class EventDateDetailReadModel(EventDateReadModel):
    """The event-date page and the API detail (`EventDateSchema`)."""

    event: EventDetailReadModel


class EventListItemReadModel(BaseReadModel):
    """A row of the public event lists (`EventListItemRefSchema`)."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class EventDateListItemReadModel(BaseReadModel):
    """A row of the public event-date lists (`EventDateListRefSchema`). Event dates
    are not trackable, so the schema's audit fields stay absent."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    start: datetime
