from project.domain.events.nested.image_for_event import ImageForEvent
from project.domain.models.value_objects.location_value_object import (
    LocationValueObject,
)
from project.domain.types import (
    ObjectId,
    OptionalChangedOptionalValue,
    OptionalChangedValue,
)
from project.domain.types.optional_changed_value_field_factory import (
    OptionalChangedValueField,
)

from .base import Event


class EventOrganizerUpdated(Event):
    id: ObjectId
    admin_unit_id: ObjectId
    name: OptionalChangedValue[str] = OptionalChangedValueField()
    url: OptionalChangedOptionalValue[str] = OptionalChangedValueField()
    email: OptionalChangedOptionalValue[str] = OptionalChangedValueField()
    phone: OptionalChangedOptionalValue[str] = OptionalChangedValueField()
    fax: OptionalChangedOptionalValue[str] = OptionalChangedValueField()
    location: OptionalChangedOptionalValue[LocationValueObject] = (
        OptionalChangedValueField()
    )
    logo: OptionalChangedOptionalValue[ImageForEvent] = OptionalChangedValueField()
