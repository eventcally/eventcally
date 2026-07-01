import datetime
from typing import List, Set

from project.domain.events.nested.image_for_event import ImageForEvent
from project.domain.models.entities.event_date_entity import EventDateEntity
from project.domain.models.enums.event_attendance_mode import EventAttendanceMode
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_status import EventStatus
from project.domain.models.enums.event_target_group_origin import EventTargetGroupOrigin
from project.domain.models.value_objects.event_date_definition_value_object import (
    EventDateDefinitionValueObject,
)
from project.domain.types import ObjectId, OptionalChangedOptionalValue
from project.domain.types.changed_value import OptionalChangedValue
from project.domain.types.optional_changed_value_field_factory import (
    OptionalChangedValueField,
)

from .base import Event


class EventUpdated(Event):
    id: ObjectId
    admin_unit_id: ObjectId
    name: OptionalChangedValue[str] = OptionalChangedValueField()
    photo: OptionalChangedOptionalValue[ImageForEvent] = OptionalChangedValueField()
    organizer_id: OptionalChangedValue[ObjectId] = OptionalChangedValueField()
    event_place_id: OptionalChangedValue[ObjectId] = OptionalChangedValueField()
    date_definitions: OptionalChangedValue[List[EventDateDefinitionValueObject]] = (
        OptionalChangedValueField()
    )
    dates: OptionalChangedValue[List[EventDateEntity]] = OptionalChangedValueField()
    status: OptionalChangedValue[EventStatus] = OptionalChangedValueField()
    public_status: OptionalChangedValue[EventPublicStatus] = OptionalChangedValueField()
    description: OptionalChangedOptionalValue[str] = OptionalChangedValueField()
    external_link: OptionalChangedOptionalValue[str] = OptionalChangedValueField()
    ticket_link: OptionalChangedOptionalValue[str] = OptionalChangedValueField()
    tags: OptionalChangedOptionalValue[str] = OptionalChangedValueField()
    internal_tags: OptionalChangedOptionalValue[str] = OptionalChangedValueField()
    kid_friendly: OptionalChangedOptionalValue[bool] = OptionalChangedValueField()
    accessible_for_free: OptionalChangedOptionalValue[bool] = (
        OptionalChangedValueField()
    )
    age_from: OptionalChangedOptionalValue[int] = OptionalChangedValueField()
    age_to: OptionalChangedOptionalValue[int] = OptionalChangedValueField()
    registration_required: OptionalChangedOptionalValue[bool] = (
        OptionalChangedValueField()
    )
    booked_up: OptionalChangedOptionalValue[bool] = OptionalChangedValueField()
    expected_participants: OptionalChangedOptionalValue[int] = (
        OptionalChangedValueField()
    )
    price_info: OptionalChangedOptionalValue[str] = OptionalChangedValueField()
    target_group_origin: OptionalChangedOptionalValue[EventTargetGroupOrigin] = (
        OptionalChangedValueField()
    )
    attendance_mode: OptionalChangedOptionalValue[EventAttendanceMode] = (
        OptionalChangedValueField()
    )
    previous_start_date: OptionalChangedOptionalValue[datetime.datetime] = (
        OptionalChangedValueField()
    )
    category_ids: OptionalChangedValue[Set[ObjectId]] = OptionalChangedValueField()
    custom_category_ids: OptionalChangedValue[Set[ObjectId]] = (
        OptionalChangedValueField()
    )
    rating: OptionalChangedOptionalValue[int] = OptionalChangedValueField()
    co_organizer_ids: OptionalChangedValue[Set[ObjectId]] = OptionalChangedValueField()
