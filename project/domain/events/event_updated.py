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
from project.domain.types import ChangedValue, ObjectId
from project.domain.types.optional_changed_value_field_factory import (
    OptionalChangedValueField,
)

from .base import Event


class EventUpdated(Event):
    id: ObjectId
    admin_unit_id: ObjectId
    name: Optional[ChangedValue[str]] = OptionalChangedValueField()
    photo: Optional[ChangedValue[ImageForEvent]] = OptionalChangedValueField()
    organizer_id: Optional[ChangedValue[ObjectId]] = OptionalChangedValueField()
    event_place_id: Optional[ChangedValue[ObjectId]] = OptionalChangedValueField()
    date_definitions: Optional[ChangedValue[List[EventDateDefinitionValueObject]]] = (
        OptionalChangedValueField()
    )
    dates: Optional[ChangedValue[List[EventDateEntity]]] = OptionalChangedValueField()
    status: Optional[ChangedValue[EventStatus]] = OptionalChangedValueField()
    public_status: Optional[ChangedValue[EventPublicStatus]] = (
        OptionalChangedValueField()
    )
    description: Optional[ChangedValue[str]] = OptionalChangedValueField()
    external_link: Optional[ChangedValue[str]] = OptionalChangedValueField()
    ticket_link: Optional[ChangedValue[str]] = OptionalChangedValueField()
    tags: Optional[ChangedValue[str]] = OptionalChangedValueField()
    internal_tags: Optional[ChangedValue[str]] = OptionalChangedValueField()
    kid_friendly: Optional[ChangedValue[bool]] = OptionalChangedValueField()
    accessible_for_free: Optional[ChangedValue[bool]] = OptionalChangedValueField()
    age_from: Optional[ChangedValue[int]] = OptionalChangedValueField()
    age_to: Optional[ChangedValue[int]] = OptionalChangedValueField()
    registration_required: Optional[ChangedValue[bool]] = OptionalChangedValueField()
    booked_up: Optional[ChangedValue[bool]] = OptionalChangedValueField()
    expected_participants: Optional[ChangedValue[int]] = OptionalChangedValueField()
    price_info: Optional[ChangedValue[str]] = OptionalChangedValueField()
    target_group_origin: Optional[ChangedValue[EventTargetGroupOrigin]] = (
        OptionalChangedValueField()
    )
    attendance_mode: Optional[ChangedValue[EventAttendanceMode]] = (
        OptionalChangedValueField()
    )
    previous_start_date: Optional[ChangedValue[datetime.datetime]] = (
        OptionalChangedValueField()
    )
    category_ids: Optional[ChangedValue[List[ObjectId]]] = OptionalChangedValueField()
    custom_category_ids: Optional[ChangedValue[List[ObjectId]]] = (
        OptionalChangedValueField()
    )
    rating: Optional[ChangedValue[int]] = OptionalChangedValueField()
    co_organizer_ids: Optional[ChangedValue[List[ObjectId]]] = (
        OptionalChangedValueField()
    )
