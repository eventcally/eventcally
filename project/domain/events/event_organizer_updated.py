from typing import Optional

from project.domain.events.nested.image_for_event import ImageForEvent
from project.domain.models.value_objects.location_value_object import (
    LocationValueObject,
)
from project.domain.types import ChangedValue, ObjectId
from project.domain.types.optional_changed_value_field_factory import (
    OptionalChangedValueField,
)

from .base import Event


class EventOrganizerUpdated(Event):
    id: ObjectId
    admin_unit_id: ObjectId
    name: Optional[ChangedValue[str]] = OptionalChangedValueField()
    url: Optional[ChangedValue[str]] = OptionalChangedValueField()
    email: Optional[ChangedValue[str]] = OptionalChangedValueField()
    phone: Optional[ChangedValue[str]] = OptionalChangedValueField()
    fax: Optional[ChangedValue[str]] = OptionalChangedValueField()
    location: Optional[ChangedValue[LocationValueObject]] = OptionalChangedValueField()
    logo: Optional[ChangedValue[ImageForEvent]] = OptionalChangedValueField()
