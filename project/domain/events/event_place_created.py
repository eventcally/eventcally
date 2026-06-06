from typing import Optional

from project.domain.events.nested.image_for_event import ImageForEvent
from project.domain.models.value_objects.location_value_object import (
    LocationValueObject,
)
from project.domain.types import ObjectId

from .base import Event


class EventPlaceCreated(Event):
    id: ObjectId
    admin_unit_id: ObjectId
    name: str
    url: Optional[str] = None
    description: Optional[str] = None
    location: Optional[LocationValueObject] = None
    photo: Optional[ImageForEvent] = None
