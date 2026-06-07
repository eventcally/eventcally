import datetime
from typing import List

from project.domain.models.enums.event_attendance_mode import EventAttendanceMode
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_status import EventStatus
from project.domain.models.enums.event_target_group_origin import EventTargetGroupOrigin
from project.domain.models.value_objects.event_date_definition_value_object import (
    EventDateDefinitionValueObject,
)
from project.domain.models.value_objects.image_value_object import ImageValueObject
from project.domain.types import ObjectId
from project.domain.types.unset_field_factory import UnsetField
from project.domain.types.unsetable import NullableUnsetable, Unsetable

from .base import Command


class UpdateEventCommand(Command):
    id: ObjectId
    name: Unsetable[str] = UnsetField()
    organizer_id: Unsetable[ObjectId] = UnsetField()
    event_place_id: Unsetable[ObjectId] = UnsetField()
    date_definitions: Unsetable[List[EventDateDefinitionValueObject]] = UnsetField()
    status: Unsetable[EventStatus] = UnsetField()
    public_status: Unsetable[EventPublicStatus] = UnsetField()
    description: NullableUnsetable[str] = UnsetField()
    external_link: NullableUnsetable[str] = UnsetField()
    ticket_link: NullableUnsetable[str] = UnsetField()
    tags: NullableUnsetable[str] = UnsetField()
    internal_tags: NullableUnsetable[str] = UnsetField()
    kid_friendly: NullableUnsetable[bool] = UnsetField()
    accessible_for_free: NullableUnsetable[bool] = UnsetField()
    age_from: NullableUnsetable[int] = UnsetField()
    age_to: NullableUnsetable[int] = UnsetField()
    registration_required: NullableUnsetable[bool] = UnsetField()
    booked_up: NullableUnsetable[bool] = UnsetField()
    expected_participants: NullableUnsetable[int] = UnsetField()
    price_info: NullableUnsetable[str] = UnsetField()
    target_group_origin: NullableUnsetable[EventTargetGroupOrigin] = UnsetField()
    attendance_mode: NullableUnsetable[EventAttendanceMode] = UnsetField()
    photo: NullableUnsetable[ImageValueObject] = UnsetField()
    previous_start_date: NullableUnsetable[datetime.datetime] = UnsetField()
    category_ids: NullableUnsetable[List[ObjectId]] = UnsetField()
    custom_category_ids: NullableUnsetable[List[ObjectId]] = UnsetField()
    rating: NullableUnsetable[int] = UnsetField()
    co_organizer_ids: NullableUnsetable[List[ObjectId]] = UnsetField()
