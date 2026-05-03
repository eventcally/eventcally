from typing import Optional

from project.domain.events.image_updated import ImageUpdated
from project.domain.events.location_updated import LocationUpdated
from project.domain.types import ChangedValue, ObjectId, Unsetable
from project.domain.types.optional_changed_value_field_factory import (
    OptionalChangedValueField,
)
from project.domain.types.unset_field_factory import UnsetField

from .base import Event


class EventPlaceUpdated(Event):
    id: ObjectId
    admin_unit_id: ObjectId
    name: Optional[ChangedValue[str]] = OptionalChangedValueField()
    url: Optional[ChangedValue[str]] = OptionalChangedValueField()
    description: Optional[ChangedValue[str]] = OptionalChangedValueField()
    location: Unsetable[LocationUpdated] = UnsetField()
    photo: Unsetable[ImageUpdated] = UnsetField()
