import datetime
from typing import List, Optional

from project.domain.events.nested.image_for_event import ImageForEvent
from project.domain.models.entities.event_date_entity import EventDateEntity
from project.domain.models.enums.event_attendance_mode import EventAttendanceMode
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_status import EventStatus
from project.domain.models.enums.event_target_group_origin import EventTargetGroupOrigin
from project.domain.models.value_objects.event_date_definition_value_object import (
    EventDateDefinitionValueObject,
)
from project.domain.types import ObjectId

from .base import Event


class EventCreated(Event):
    id: ObjectId
    admin_unit_id: ObjectId
    name: str
    photo: Optional[ImageForEvent] = None
    organizer_id: ObjectId
    event_place_id: ObjectId
    date_definitions: List[EventDateDefinitionValueObject]
    dates: List[EventDateEntity]
    status: EventStatus = EventStatus.scheduled
    public_status: EventPublicStatus = EventPublicStatus.published
    description: Optional[str] = None
    external_link: Optional[str] = None
    ticket_link: Optional[str] = None
    tags: Optional[str] = None
    internal_tags: Optional[str] = None
    kid_friendly: Optional[bool] = None
    accessible_for_free: Optional[bool] = None
    age_from: Optional[int] = None
    age_to: Optional[int] = None
    registration_required: Optional[bool] = None
    booked_up: Optional[bool] = None
    expected_participants: Optional[int] = None
    price_info: Optional[str] = None
    target_group_origin: Optional[EventTargetGroupOrigin] = None
    attendance_mode: Optional[EventAttendanceMode] = None
    previous_start_date: Optional[datetime.datetime] = None
    category_ids: Optional[List[ObjectId]] = None
    custom_category_ids: Optional[List[ObjectId]] = None
    rating: Optional[int] = None
    co_organizer_ids: Optional[List[ObjectId]] = None
